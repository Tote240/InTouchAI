import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_ml_kit/google_ml_kit.dart';

class PrediccionSena {
  final String etiqueta;
  final double confianza;
  final List<Offset> landmarks;

  PrediccionSena(this.etiqueta, this.confianza, this.landmarks);
}

class Predictor {
  final String baseUrl = 'http://192.168.151.100:5000'; // Ajusta esta IP
  late final poseDetector = GoogleMlKit.vision.poseDetector();
  
  List<String> _gestos = [];
  CameraController? _cameraController;
  String? _error;
  List<CameraDescription>? _cameras;
  
  // Buffer para acumular frames
  List<List<double>> _frameBuffer = [];
  static const int REQUIRED_FRAMES = 5;
  
  CameraController? get cameraController => _cameraController;
  List<String> getGestos() => _gestos;
  String? get error => _error;

  Future<void> inicializar({bool usarCamaraFrontal = true}) async {
    try {
      print('⌛ Iniciando inicialización del predictor');

      if (_cameras == null) {
        _cameras = await availableCameras();
      }

      if (_cameras!.isEmpty) throw Exception('No se encontraron cámaras');

      final camaraSeleccionada = usarCamaraFrontal
          ? _cameras!.firstWhere(
              (camera) => camera.lensDirection == CameraLensDirection.front,
              orElse: () => _cameras!.first)
          : _cameras!.firstWhere(
              (camera) => camera.lensDirection == CameraLensDirection.back,
              orElse: () => _cameras!.first);

      _cameraController = CameraController(
        camaraSeleccionada,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.bgra8888,
      );

      print('⌛ Inicializando cámara...');
      await _cameraController!.initialize();
      
      // Configurar cámara
      await _cameraController!.setExposureMode(ExposureMode.auto);
      await _cameraController!.setFocusMode(FocusMode.auto);
      await _cameraController!.setFlashMode(FlashMode.off);
      
      print('✅ Cámara inicializada');

      // Cargar gestos
      await _cargarGestos();

      // Limpiar buffer
      _frameBuffer.clear();

    } catch (e) {
      print('❌ Error en inicialización: $e');
      _error = e.toString();
      rethrow;
    }
  }

  Future<void> _cargarGestos() async {
    try {
      print('⌛ Conectando a: $baseUrl/gestures');
      final response = await http.get(
        Uri.parse('$baseUrl/gestures'),
        headers: {'Accept': 'application/json'},
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data != null && data['gestures'] != null) {
          _gestos = List<String>.from(data['gestures']);
          print('✅ Gestos cargados: $_gestos');
        }
      } else {
        throw Exception('Error al cargar gestos: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Error cargando gestos: $e');
      rethrow;
    }
  }

  Future<PrediccionSena?> predecir(CameraImage imagen) async {
    try {
      final inputImage = InputImage.fromBytes(
        bytes: _concatenatePlanes(imagen.planes),
        metadata: InputImageMetadata(
          size: Size(imagen.width.toDouble(), imagen.height.toDouble()),
          rotation: InputImageRotation.rotation0deg,
          format: InputImageFormat.bgra8888,
          bytesPerRow: imagen.planes[0].bytesPerRow,
        ),
      );

      final poses = await poseDetector.processImage(inputImage);
      
      if (poses.isEmpty) {
        print('No se detectaron poses');
        return PrediccionSena('No se detectó mano', 0.0, []);
      }

      final pose = poses.first;
      final List<double> landmarks = [];
      final List<Offset> visualLandmarks = [];

      // Procesar landmarks
      pose.landmarks.forEach((key, point) {
        landmarks.addAll([
          point.x / imagen.width,
          point.y / imagen.height,
          point.z / 0.0,
        ]);
        
        visualLandmarks.add(Offset(
          point.x,
          point.y,
        ));
      });

      // Añadir al buffer
      _frameBuffer.add(landmarks);
      print('Buffer frames: ${_frameBuffer.length}/$REQUIRED_FRAMES');
      
      if (_frameBuffer.length < REQUIRED_FRAMES) {
        return PrediccionSena('Procesando...', 0.0, visualLandmarks);
      }

      // Enviar predicción
      final prediction = await _enviarPrediccion(visualLandmarks);
      _frameBuffer.clear();
      return prediction;

    } catch (e) {
      print('❌ Error en predicción: $e');
      return null;
    }
  }

  Future<PrediccionSena?> _enviarPrediccion(List<Offset> visualLandmarks) async {
    try {
      final Map<String, dynamic> requestData = {
        'landmarks_sequence': _frameBuffer,
      };

      print('📤 Enviando secuencia al servidor...');
      final response = await http.post(
        Uri.parse('$baseUrl/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(requestData),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PrediccionSena(
          data['gesture'],
          (data['confidence'] as num).toDouble(),
          visualLandmarks,
        );
      }

      print('❌ Error en la respuesta: ${response.statusCode}');
      return null;
    } catch (e) {
      print('❌ Error enviando predicción: $e');
      return null;
    }
  }

  Uint8List _concatenatePlanes(List<Plane> planes) {
    final WriteBuffer allBytes = WriteBuffer();
    for (final plane in planes) {
      allBytes.putUint8List(plane.bytes);
    }
    return allBytes.done().buffer.asUint8List();
  }

  Future<void> dispose() async {
    await _cameraController?.dispose();
    await poseDetector.close();
    _cameraController = null;
    _frameBuffer.clear();
  }
}