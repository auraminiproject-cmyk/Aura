import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_provider.dart';

class WardrobeScreen extends ConsumerStatefulWidget {
  const WardrobeScreen({super.key});

  @override
  ConsumerState<WardrobeScreen> createState() => _WardrobeScreenState();
}

class _WardrobeScreenState extends ConsumerState<WardrobeScreen> {
  List<dynamic> _items = [];
  bool _loading = false;

  Future<void> _load() async {
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) return;

    final api = ref.read(apiClientProvider);
    setState(() => _loading = true);
    try {
      final items = await api.listWardrobe();
      setState(() => _items = items);
    } catch (_) {
      // Silently fail if offline
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _add() async {
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⚠️ Cannot add items while offline')),
      );
      return;
    }

    final api = ref.read(apiClientProvider);
    await api.addWardrobeItem(name: 'Saved outfit ${DateTime.now().hour}:${DateTime.now().minute}');
    await _load();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Wardrobe'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _add,
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.checkroom_outlined, size: 64, color: Colors.grey.shade400),
                      const SizedBox(height: 12),
                      Text('No saved items yet',
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 16)),
                      const SizedBox(height: 8),
                      Text('Tap + to add items to your wardrobe',
                          style: TextStyle(color: Colors.grey.shade500)),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: _items.length,
                  itemBuilder: (_, i) {
                    final item = _items[i] as Map<String, dynamic>;
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                        child: const Icon(Icons.checkroom),
                      ),
                      title: Text('${item['name']}'),
                      subtitle: Text('${item['category'] ?? 'Uncategorized'}'),
                    );
                  },
                ),
    );
  }
}
