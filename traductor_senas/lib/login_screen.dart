import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  bool _isHandVisible = false;

  void _handleLogin() {
    // Lógica para simular el inicio de sesión
    String email = _emailController.text;
    String password = _passwordController.text;

    if (email == 'ia@gmail.com' && password == '123') {
      // Simulamos que el inicio de sesión fue exitoso
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Inicio de sesión exitoso')),
      );
      // Aquí podrías redirigir a otra pantalla
    } else {
      // Si las credenciales no son correctas
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Correo o contraseña incorrectos')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Iniciar sesión'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 40),
            const Icon(
              Icons.account_circle,
              size: 100,
              color: Colors.blue,
            ),
            const SizedBox(height: 40),
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                labelText: 'Correo electrónico',
                prefixIcon: const Icon(Icons.email),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(
                labelText: 'Contraseña',
                prefixIcon: const Icon(Icons.lock),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: () {
                // Lógica de inicio de sesión con las credenciales capturadas
                setState(() {
                  _isHandVisible = !_isHandVisible; // Animación de la mano
                });
                _handleLogin(); // Llamar a la función de inicio de sesión
              },
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              child: const Text(
                'Iniciar sesión',
                style: TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(height: 40),
            // Animación de la mano relacionada con el lenguaje de señas
            AnimatedContainer(
              duration: const Duration(seconds: 1),
              width: _isHandVisible ? 100 : 0,
              height: _isHandVisible ? 100 : 0,
              child: Icon(
                Icons.pan_tool,
                color: Colors.blue,
                size: 100,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
