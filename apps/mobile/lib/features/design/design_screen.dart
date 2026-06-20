import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/api_provider.dart';

class DesignScreen extends ConsumerStatefulWidget {
  const DesignScreen({super.key});

  @override
  ConsumerState<DesignScreen> createState() => _DesignScreenState();
}

class _DesignScreenState extends ConsumerState<DesignScreen> {
  final _briefController = TextEditingController(
    text: 'Red gold lehenga for Hyderabad wedding, budget 5000',
  );
  bool _loading = false;
  List<Map<String, dynamic>> _variants = [];

  Future<void> _generate() async {
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⚠️ Cannot generate while offline')),
      );
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() => _loading = true);
    try {
      final resp = await api.generateOutfits(brief: _briefController.text.trim());
      final list = (resp['variants'] as List?)?.cast<Map<String, dynamic>>() ?? [];
      setState(() => _variants = list);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Outfit Design')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _briefController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Design brief',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: _loading ? null : _generate,
            child: Text(_loading ? 'Generating...' : 'Generate Outfits'),
          ),
          if (_loading) ...[
            const SizedBox(height: 16),
            const LinearProgressIndicator(),
            const Text('Stage: LCM preview...'),
          ],
          const SizedBox(height: 16),
          ..._variants.map((v) {
            final bytes = ApiClient.decodeVariantImage(v);
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Column(
                children: [
                  if (bytes != null)
                    Image.memory(Uint8List.fromList(bytes), height: 200, fit: BoxFit.cover)
                  else
                    const SizedBox(height: 120, child: Icon(Icons.image, size: 48)),
                  Padding(
                    padding: const EdgeInsets.all(8),
                    child: Text(
                      'CLIP ${(v['clip_score'] as num?)?.toStringAsFixed(2) ?? "?"}',
                    ),
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.thumb_up),
                        onPressed: () => ref.read(apiClientProvider).styleFeedback(
                              liked: true,
                              tags: ['ethnic', 'wedding'],
                            ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.thumb_down),
                        onPressed: () => ref.read(apiClientProvider).styleFeedback(
                              liked: false,
                              tags: ['ethnic'],
                            ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
