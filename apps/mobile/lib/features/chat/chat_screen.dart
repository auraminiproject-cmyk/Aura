import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:record/record.dart';
import 'dart:io';
import 'dart:convert';

import '../../core/api_provider.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _messages = <Map<String, String>>[];
  String? _sessionId;
  bool _loading = false;
  bool _recording = false;
  final _recorder = AudioRecorder();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _recorder.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      _addMessage('assistant', '⚠️ You are offline. Please connect to the server first.');
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() {
      _loading = true;
      _messages.add({'role': 'user', 'text': text});
      _controller.clear();
    });
    _scrollToBottom();

    try {
      final resp = await api.sendChat(
        message: text,
        sessionId: _sessionId,
        language: 'te',
      );
      _sessionId = resp['session_id'] as String?;
      final reply = resp['reply'] as String;
      final products = resp['products'] as List?;
      var replyText = reply;
      if (products != null && products.isNotEmpty) {
        replyText += '\n\n🛍 ${products.length} products matched';
      }
      if (resp['outfits'] != null) {
        final variants = (resp['outfits']['variants'] as List?)?.length ?? 0;
        if (variants > 0) replyText += '\n👗 $variants outfit previews ready';
      }
      _addMessage('assistant', replyText);
    } catch (e) {
      _addMessage('assistant', '❌ API error — is the server running?\nuvicorn services.api.main:app --port 8000');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _addMessage(String role, String text) {
    setState(() {
      _messages.add({'role': role, 'text': text});
    });
    _scrollToBottom();
  }

  Future<void> _toggleRecording() async {
    if (_recording) {
      // Stop recording
      final path = await _recorder.stop();
      setState(() => _recording = false);

      if (path != null) {
        _addMessage('user', '🎤 Voice message sent…');
        setState(() => _loading = true);

        try {
          final file = File(path);
          final bytes = await file.readAsBytes();
          final b64 = base64Encode(bytes);

          final api = ref.read(apiClientProvider);
          // Send as text for now — the backend will transcribe
          final resp = await api.sendChat(
            message: '[AUDIO:$b64]',
            sessionId: _sessionId,
            language: 'te',
          );
          _sessionId = resp['session_id'] as String?;
          _addMessage('assistant', resp['reply'] as String);
        } catch (e) {
          _addMessage('assistant', '❌ Voice processing failed: $e');
        } finally {
          setState(() => _loading = false);
        }
      }
    } else {
      // Check permission and start recording
      if (await _recorder.hasPermission()) {
        await _recorder.start(const RecordConfig(), path: '');
        setState(() => _recording = true);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission denied. Please enable it in Settings.')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final connState = ref.watch(connectionStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Fashion Stylist'),
        actions: [
          if (connState == AppConnectionState.online)
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Icon(Icons.circle, color: Colors.green, size: 10),
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey.shade400),
                        const SizedBox(height: 16),
                        Text(
                          'Ask me about fashion!\n"Wedding ki outfit suggest cheyyi"',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) {
                      final m = _messages[i];
                      final isUser = m['role'] == 'user';
                      return Align(
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.78,
                          ),
                          decoration: BoxDecoration(
                            color: isUser
                                ? Theme.of(context).colorScheme.primaryContainer
                                : Colors.grey.shade200,
                            borderRadius: BorderRadius.only(
                              topLeft: const Radius.circular(16),
                              topRight: const Radius.circular(16),
                              bottomLeft: Radius.circular(isUser ? 16 : 4),
                              bottomRight: Radius.circular(isUser ? 4 : 16),
                            ),
                          ),
                          child: Text(m['text'] ?? ''),
                        ),
                      );
                    },
                  ),
          ),
          if (_loading) const LinearProgressIndicator(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  // Mic button
                  IconButton(
                    icon: Icon(
                      _recording ? Icons.stop_circle : Icons.mic,
                      color: _recording ? Colors.red : null,
                    ),
                    onPressed: _toggleRecording,
                    tooltip: _recording ? 'Stop recording' : 'Voice input',
                  ),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: InputDecoration(
                        hintText: 'Wedding ki outfit cheppandi...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 4),
                  IconButton.filled(
                    icon: const Icon(Icons.send),
                    onPressed: _send,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
