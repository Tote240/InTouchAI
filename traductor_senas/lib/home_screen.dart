import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'predictor.dart';
import 'login_screen.dart';
import 'dictionaries_screen.dart';
import 'payment_plans_screen.dart';

class PaginaPrincipal extends StatefulWidget {
  const PaginaPrincipal({super.key});

  @override
  State<PaginaPrincipal> createState() => _EstadoPaginaPrincipal();
}

class _EstadoPaginaPrincipal extends State<PaginaPrincipal>
    with SingleTickerProviderStateMixin {
  final Predictor _predictor = Predictor();
  String _senaActual = '';
  double _confianza = 0.0;
  bool _inicializando = true;
  String? _error;
  List<String> _gestosDisponibles = [];
  bool _camaraFrontal = true;
  List<Offset> _handPoints = [];
  bool _procesando = false;

  late AnimationController _animationController;
  late Animation<double> _opacityAnimation;

  @override
  void initState() {
    super.initState();
    _inicializarPredictor();

    _animationController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _opacityAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeIn,
      ),
    );
  }

  Future<void> _inicializarPredictor() async {
    try {
      await _predictor.inicializar(usarCamaraFrontal: _camaraFrontal);
      _gestosDisponibles = _predictor.getGestos();

      if (mounted) {
        setState(() {
          _inicializando = false;
        });
      }

      _iniciarDeteccion();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = _predictor.error;
          _inicializando = false;
        });
      }
    }
  }

  void _iniciarDeteccion() {
    const duration = Duration(milliseconds: 500);

    _predictor.cameraController?.startImageStream((image) async {
      if (_procesando) return;
      _procesando = true;

      try {
        final prediccion = await _predictor.predecir(image);
        if (prediccion != null && prediccion.confianza >= 0.3 && mounted) {
          setState(() {
            _senaActual = prediccion.etiqueta;
            _confianza = prediccion.confianza;
            _handPoints = prediccion.landmarks;
          });
        }
      } catch (e) {
        print('Error en detección: $e');
      } finally {
        await Future.delayed(duration);
        _procesando = false;
      }
    });
  }

  Future<void> _cambiarCamara() async {
    setState(() {
      _inicializando = true;
      _camaraFrontal = !_camaraFrontal;
    });

    await _predictor.dispose();
    await _inicializarPredictor();
  }

  void _mostrarGestosDisponibles() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Text(
                'Gestos Disponibles',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            Expanded(
              child: ListView.builder(
                itemCount: _gestosDisponibles.length,
                itemBuilder: (context, index) => ListTile(
                  title: Text(_gestosDisponibles[index]),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_inicializando) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $_error'),
              ElevatedButton(
                onPressed: _inicializarPredictor,
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Traductor de Señas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.login),
            onPressed: () {
              Navigator.push(
                context,
                PageRouteBuilder(
                  pageBuilder: (context, animation, secondaryAnimation) =>
                      const LoginScreen(),
                  transitionsBuilder:
                      (context, animation, secondaryAnimation, child) {
                    return FadeTransition(
                      opacity: animation,
                      child: child,
                    );
                  },
                ),
              );
            },
            tooltip: 'Iniciar sesión',
          ),
          IconButton(
            icon: const Icon(Icons.library_books),
            onPressed: () {
              Navigator.push(
                context,
                PageRouteBuilder(
                  pageBuilder: (context, animation, secondaryAnimation) =>
                      const DictionariesScreen(),
                  transitionsBuilder:
                      (context, animation, secondaryAnimation, child) {
                    return SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(1.0, 0.0),
                        end: Offset.zero,
                      ).animate(animation),
                      child: child,
                    );
                  },
                ),
              );
            },
            tooltip: 'Diccionarios',
          ),
          IconButton(
            icon: const Icon(Icons.monetization_on),
            onPressed: () {
              Navigator.push(
                context,
                PageRouteBuilder(
                  pageBuilder: (context, animation, secondaryAnimation) =>
                      const PaymentPlansScreen(),
                  transitionsBuilder:
                      (context, animation, secondaryAnimation, child) {
                    return ScaleTransition(
                      scale: Tween<double>(begin: 0.0, end: 1.0).animate(
                        CurvedAnimation(
                          parent: animation,
                          curve: Curves.fastOutSlowIn,
                        ),
                      ),
                      child: child,
                    );
                  },
                ),
              );
            },
            tooltip: 'Planes',
          ),
        ],
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Vista previa de la cámara
          if (_predictor.cameraController != null)
            CameraPreview(_predictor.cameraController!),

          // Guía visual
          CustomPaint(
            painter: GuidePainter(),
          ),

          // Visualización de manos
          if (_handPoints.isNotEmpty)
            CustomPaint(
              painter: HandOverlay(_handPoints),
            ),

          // Panel de información
          Positioned(
            bottom: 20,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 16,
              ),
              color: Colors.black54,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _senaActual,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (_confianza > 0)
                    Text(
                      'Confianza: ${(_confianza * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 16,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomAppBar(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            IconButton(
              icon: Icon(_camaraFrontal ? Icons.camera_rear : Icons.camera_front),
              onPressed: _cambiarCamara,
              tooltip: 'Cambiar cámara',
            ),
            IconButton(
              icon: const Icon(Icons.list),
              onPressed: _mostrarGestosDisponibles,
              tooltip: 'Gestos disponibles',
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _predictor.dispose();
    _animationController.dispose();
    super.dispose();
  }
}

class GuidePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.green
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final double width = size.width * 0.6;
    final double height = size.height * 0.6;
    final double left = (size.width - width) / 2;
    final double top = (size.height - height) / 2;

    canvas.drawRect(
      Rect.fromLTWH(left, top, width, height),
      paint,
    );

    final textPainter = TextPainter(
      text: const TextSpan(
        text: 'Coloque su mano aquí',
        style: TextStyle(
          color: Colors.white,
          fontSize: 16,
          shadows: [
            Shadow(
              blurRadius: 3.0,
              color: Colors.black,
              offset: Offset(1, 1),
            ),
          ],
        ),
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    );

    textPainter.layout(minWidth: 0, maxWidth: size.width);
    textPainter.paint(
      canvas,
      Offset((size.width - textPainter.width) / 2, top - 25),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class HandOverlay extends CustomPainter {
  final List<Offset> points;

  HandOverlay(this.points);

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty) {
      return;
    }

    final paint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final dotPaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 4
      ..style = PaintingStyle.fill;

    // Dibujar conexiones entre puntos
    if (points.length >= 21) {
      // Conexiones de los dedos
      _drawFingerConnections(canvas, paint, [0, 1, 2, 3, 4]);    // Pulgar
      _drawFingerConnections(canvas, paint, [0, 5, 6, 7, 8]);    // Índice
      _drawFingerConnections(canvas, paint, [0, 9, 10, 11, 12]); // Medio
      _drawFingerConnections(canvas, paint, [0, 13, 14, 15, 16]); // Anular
      _drawFingerConnections(canvas, paint, [0, 17, 18, 19, 20]); // Meñique

      // Conexiones de la palma
      canvas.drawLine(points[0], points[5], paint);
      canvas.drawLine(points[5], points[9], paint);
      canvas.drawLine(points[9], points[13], paint);
      canvas.drawLine(points[13], points[17], paint);
    }

    // Dibujar puntos
    for (var point in points) {
      canvas.drawCircle(point, 4, dotPaint);
    }
  }

  void _drawFingerConnections(Canvas canvas, Paint paint, List<int> indices) {
    for (int i = 0; i < indices.length - 1; i++) {
      canvas.drawLine(
        points[indices[i]],
        points[indices[i + 1]],
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}