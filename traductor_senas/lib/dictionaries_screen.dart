import 'package:flutter/material.dart';

class DictionariesScreen extends StatelessWidget {
  const DictionariesScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Diccionarios'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildDictionaryCard(
            context,
            'Diccionario Lenguaje Chileno',
            'Explora el lenguaje de señas chileno y aprende a comunicarte de manera efectiva. Este diccionario cuenta con una amplia colección de señas utilizadas en Chile, junto con ilustraciones claras y explicaciones detalladas para cada una de ellas.',
            'Gratis',
          ),
          _buildDictionaryCard(
            context,
            'Diccionario Lengua Peruana',
            'Sumérgete en el fascinante mundo del lenguaje de señas peruano. Con este diccionario, podrás aprender las señas más comunes utilizadas en Perú, acompañadas de imágenes nítidas y descripciones precisas para facilitar tu aprendizaje.',
            '\$12,000 CLP',
          ),
          _buildDictionaryCard(
            context,
            'Diccionario Lenguaje Mexicano',
            'Descubre la riqueza del lenguaje de señas mexicano con este completo diccionario. Encontrarás una extensa variedad de señas utilizadas en México, junto con explicaciones claras y ejemplos visuales para ayudarte a dominar este lenguaje.',
            '\$12,000 CLP',
          ),
          _buildDictionaryCard(
            context,
            'Diccionario Lengua Argentina',
            'Adéntrate en el lenguaje de señas argentino y amplía tus habilidades de comunicación. Este diccionario te brinda acceso a una amplia gama de señas utilizadas en Argentina, acompañadas de ilustraciones detalladas y explicaciones concisas.',
            '\$12,000 CLP',
          ),
          _buildDictionaryCard(
            context,
            'Diccionario Lenguaje Colombiano',
            'Explora el fascinante lenguaje de señas colombiano con este completo diccionario. Encontrarás una gran variedad de señas utilizadas en Colombia, junto con imágenes claras y descripciones precisas para facilitar tu aprendizaje y mejorar tu comunicación.',
            '\$12,000 CLP',
          ),
        ],
      ),
    );
  }

  Widget _buildDictionaryCard(
      BuildContext context, String title, String description, String price) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: () {
          // Navigate to dictionary details screen
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => DictionaryDetailsScreen(
                title: title,
                description: description,
                price: price,
              ),
            ),
          );
        },
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
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                price,
                style: const TextStyle(
                  fontSize: 18,
                  color: Colors.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class DictionaryDetailsScreen extends StatelessWidget {
  final String title;
  final String description;
  final String price;

  const DictionaryDetailsScreen({
    Key? key,
    required this.title,
    required this.description,
    required this.price,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              description,
              style: const TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 20),
            if (title != 'Diccionario Lenguaje Chileno') ...[
              Text(
                'Precio: $price',
                style: const TextStyle(
                  fontSize: 20,
                  color: Colors.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () {
                  // Implement the purchase functionality here
                  showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const Text('Compra'),
                      content: Text(
                          '¿Estás seguro de que deseas comprar "$title" por $price?'),
                      actions: [
                        TextButton(
                          onPressed: () {
                            Navigator.of(context).pop();
                          },
                          child: const Text('Cancelar'),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.of(context).pop();
                            // Proceed with the purchase
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text('Compra realizada con éxito')),
                            );
                          },
                          child: const Text('Comprar'),
                        ),
                      ],
                    ),
                  );
                },
                child: const Text('Comprar Ahora'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
