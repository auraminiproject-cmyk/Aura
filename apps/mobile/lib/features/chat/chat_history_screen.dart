import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_provider.dart';
import '../../core/aura_background.dart';

class ChatHistoryScreen extends ConsumerStatefulWidget {
  const ChatHistoryScreen({super.key});

  @override
  ConsumerState<ChatHistoryScreen> createState() => _ChatHistoryScreenState();
}

class _ChatHistoryScreenState extends ConsumerState<ChatHistoryScreen> {
  List<dynamic> _sessions = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadSessions();
  }

  Future<void> _loadSessions() async {
    try {
      final api = ref.read(apiClientProvider);
      final sessions = await api.getSessions();
      if (mounted) {
        setState(() {
          _sessions = sessions;
          _loading = false;
        });
      }
    } catch (e) {
      debugPrint('Failed to load sessions: $e');
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuraBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          title: const Text('Design History', style: TextStyle(fontWeight: FontWeight.w600)),
          centerTitle: true,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator(color: Color(0xFFD4AF37)))
            : _sessions.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.history, color: Colors.white24, size: 64),
                        const SizedBox(height: 16),
                        Text('No past designs found', style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _sessions.length,
                    itemBuilder: (context, index) {
                      final session = _sessions[index];
                      final title = session['title']?.toString() ?? 'New Design Session';
                      final dateStr = session['updated_at']?.toString();
                      String formattedDate = '';
                      if (dateStr != null) {
                        try {
                          final dt = DateTime.parse(dateStr).toLocal();
                          formattedDate = '${dt.day}/${dt.month}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
                        } catch (_) {}
                      }

                      return Card(
                        color: Colors.white.withValues(alpha: 0.05),
                        margin: const EdgeInsets.only(bottom: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          leading: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: const Color(0xFFD4AF37).withValues(alpha: 0.2),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.design_services, color: Color(0xFFD4AF37), size: 20),
                          ),
                          title: Text(
                            title,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: formattedDate.isNotEmpty
                              ? Text(formattedDate, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12))
                              : null,
                          trailing: const Icon(Icons.chevron_right, color: Colors.white54),
                          onTap: () {
                            Navigator.pop(context, session['id']);
                          },
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}
