import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_provider.dart';

class ProductResultsScreen extends ConsumerStatefulWidget {
  const ProductResultsScreen({super.key});

  @override
  ConsumerState<ProductResultsScreen> createState() => _ProductResultsScreenState();
}

class _ProductResultsScreenState extends ConsumerState<ProductResultsScreen> {
  final _queryController = TextEditingController(text: 'red wedding lehenga');
  List<dynamic> _products = [];
  bool _loading = false;

  Future<void> _search() async {
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('⚠️ Cannot search while offline')),
        );
      }
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() => _loading = true);
    try {
      final results = await api.searchProducts(_queryController.text.trim());
      setState(() => _products = results);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Search failed: $e')),
        );
      }
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Shop Matches')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _queryController,
                    decoration: InputDecoration(
                      hintText: 'Search outfit products',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: _loading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.search),
                  onPressed: _loading ? null : _search,
                ),
              ],
            ),
          ),
          Expanded(
            child: _products.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.shopping_bag_outlined, size: 64, color: Colors.grey.shade400),
                        const SizedBox(height: 12),
                        Text('Search for products above',
                            style: TextStyle(color: Colors.grey.shade600)),
                      ],
                    ),
                  )
                : GridView.builder(
                    padding: const EdgeInsets.all(12),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 0.72,
                    ),
                    itemCount: _products.length,
                    itemBuilder: (_, i) {
                      final p = _products[i] as Map<String, dynamic>;
                      final price = p['price_inr'];
                      return Card(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: Container(
                                color: Colors.grey.shade300,
                                width: double.infinity,
                                child: const Icon(Icons.shopping_bag, size: 40),
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.all(8),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${p['name']}', maxLines: 2, overflow: TextOverflow.ellipsis),
                                  Text('₹$price', style: const TextStyle(fontWeight: FontWeight.bold)),
                                  Text('${p['platform']}'),
                                  TextButton(
                                    onPressed: () {
                                      final url = p['affiliate_url'] as String?;
                                      if (url != null) {
                                        launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
                                      }
                                    },
                                    child: const Text('Buy Now'),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
