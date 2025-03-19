import 'package:flutter/material.dart';

class PaymentPlansScreen extends StatelessWidget {
  const PaymentPlansScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Planes de Pago'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildPlanCard(
            context,
            'Plan Individual',
            'Ideal para usuarios individuales que desean acceder a todas las funciones de la aplicación.',
            '\$5.000/mes',
          ),
          _buildPlanCard(
            context,
            'Plan Familiar',
            'Perfecto para familias que desean compartir los beneficios de la aplicación entre varios miembros.',
            '\$12.000/mes',
          ),
          // Add more payment plan cards as needed
        ],
      ),
    );
  }

  Widget _buildPlanCard(
      BuildContext context, String title, String description, String price) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              description,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  price,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                ElevatedButton(
                  onPressed: () {
                    // Handle plan selection
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text('Seleccionar'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}