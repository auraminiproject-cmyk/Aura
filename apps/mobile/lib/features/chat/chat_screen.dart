import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:audioplayers/audioplayers.dart';

import '../../core/api_provider.dart';
import '../../core/aura_background.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen>
    with SingleTickerProviderStateMixin {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _messages = <Map<String, String>>[];
  final _voiceSessionId = 'voice-default';
  bool _loading = false;
  final _audioPlayer = AudioPlayer();
  late final AnimationController _typingCtrl;

  // Speech-to-text
  final SpeechToText _speech = SpeechToText();
  bool _speechAvailable = false;
  bool _isListening = false;
  String _liveTranscript = '';

  @override
  void initState() {
    super.initState();
    _typingCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    _speechAvailable = await _speech.initialize(
      onError: (error) {
        debugPrint('Speech error: ${error.errorMsg}');
        if (mounted) {
          setState(() => _isListening = false);
        }
      },
      onStatus: (status) {
        debugPrint('Speech status: $status');
        if (status == 'done' || status == 'notListening') {
          if (mounted && _isListening) {
            _onSpeechDone();
          }
        }
      },
    );
    setState(() {});
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _audioPlayer.dispose();
    _typingCtrl.dispose();
    _speech.stop();
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

  // ── Text send (existing) ───────────────────────────────────────
  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      _addMessage('assistant',
          '⚠️ You are offline. Please connect to the server first.');
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
      // Use voice converse-text for stylist persona
      final resp = await api.voiceConverseText(
        message: text,
        sessionId: _voiceSessionId,
        language: 'te',
      );

      final replyText = resp['reply_text'] as String? ?? '';
      _addMessage('assistant', replyText);

      // Show outfit state
      final outfitState = resp['outfit_state'] as Map<String, dynamic>?;
      if (outfitState != null) {
        final stage = outfitState['stage'] as String? ?? '';
        if (stage == 'finalized') {
          _addMessage('assistant',
              '✅ Outfit finalized! Your design is being generated.');
        }
      }

      // Play reply audio if available
      final audioUrl = resp['reply_audio_url'] as String?;
      if (audioUrl != null && audioUrl.isNotEmpty) {
        try {
          await _audioPlayer.play(UrlSource(audioUrl));
        } catch (_) {}
      }
    } catch (e) {
      _addMessage('assistant',
          '❌ Could not reach the server.\nPlease check your connection.');
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

  // ── Live speech-to-text ────────────────────────────────────────
  Future<void> _toggleListening() async {
    if (_isListening) {
      await _speech.stop();
      _onSpeechDone();
    } else {
      if (!_speechAvailable) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                  '🎤 Speech recognition not available. Please check microphone permissions in Settings.'),
            ),
          );
        }
        return;
      }

      setState(() {
        _isListening = true;
        _liveTranscript = '';
      });

      await _speech.listen(
        onResult: _onSpeechResult,
        listenOptions: SpeechListenOptions(
          listenMode: ListenMode.dictation,
          partialResults: true,
          cancelOnError: true,
          autoPunctuation: true,
        ),
      );
    }
  }

  void _onSpeechResult(SpeechRecognitionResult result) {
    setState(() {
      _liveTranscript = result.recognizedWords;
      // Update text field live
      _controller.text = _liveTranscript;
      _controller.selection = TextSelection.fromPosition(
        TextPosition(offset: _controller.text.length),
      );
    });

    if (result.finalResult) {
      _onSpeechDone();
    }
  }

  void _onSpeechDone() {
    if (!_isListening) return;
    setState(() => _isListening = false);

    final text = _liveTranscript.trim();
    if (text.isNotEmpty) {
      // Auto-send the transcribed text
      _controller.text = text;
      _send();
    }
  }

  @override
  Widget build(BuildContext context) {
    final connState = ref.watch(connectionStateProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Animated AURA logo dot
            Container(
              width: 10,
              height: 10,
              margin: const EdgeInsets.only(right: 10),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: connState == AppConnectionState.online
                    ? const Color(0xFFD4AF37)
                    : Colors.grey,
                boxShadow: connState == AppConnectionState.online
                    ? [
                        BoxShadow(
                          color: const Color(0xFFD4AF37).withValues(alpha: 0.5),
                          blurRadius: 8,
                          spreadRadius: 1,
                        ),
                      ]
                    : null,
              ),
            ),
            const Text('AURA'),
            Text(
              '  Stylist',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.4),
                fontSize: 14,
                fontWeight: FontWeight.w300,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Live transcription banner
          if (_isListening)
            _buildListeningBanner(),
          Expanded(
            child: _messages.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                    itemCount: _messages.length + (_loading ? 1 : 0),
                    itemBuilder: (_, i) {
                      if (i == _messages.length && _loading) {
                        return _buildTypingIndicator();
                      }
                      return _buildMessageBubble(_messages[i]);
                    },
                  ),
          ),
          _buildInputBar(),
        ],
      ),
    );
  }

  Widget _buildListeningBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF8B1538).withValues(alpha: 0.9),
            const Color(0xFF4A148C).withValues(alpha: 0.9),
          ],
        ),
      ),
      child: Row(
        children: [
          // Pulsing mic icon
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0.8, end: 1.2),
            duration: const Duration(milliseconds: 600),
            builder: (context, value, child) {
              return Transform.scale(
                scale: _isListening ? value : 1.0,
                child: const Icon(Icons.mic, color: Colors.red, size: 22),
              );
            },
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Listening...',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.7),
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                if (_liveTranscript.isNotEmpty)
                  Text(
                    _liveTranscript,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  )
                else
                  Text(
                    'Speak now...',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.5),
                      fontSize: 14,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
              ],
            ),
          ),
          // Stop button
          GestureDetector(
            onTap: _toggleListening,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(Icons.stop, color: Colors.white, size: 18),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // AURA brand icon
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF8B1538), Color(0xFF4A148C)],
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF8B1538).withValues(alpha: 0.4),
                  blurRadius: 24,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: const Icon(
              Icons.auto_awesome,
              color: Colors.white,
              size: 36,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Your AI Fashion Stylist',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  letterSpacing: -0.3,
                ),
          ),
          const SizedBox(height: 12),
          Text(
            'Ask me about outfits, styling tips,\nor body-type recommendations',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 20),
          // Mic hint
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              color: const Color(0xFF8B1538).withValues(alpha: 0.2),
              border: Border.all(color: const Color(0xFF8B1538).withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.mic, color: Colors.white.withValues(alpha: 0.7), size: 18),
                const SizedBox(width: 8),
                Text(
                  'Tap the mic to speak',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 13),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // Quick action chips
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              _quickChip('👗 Wedding outfit'),
              _quickChip('🎨 Color for my skin tone'),
              _quickChip('📐 Body type dressing'),
              _quickChip('💰 Budget outfit under ₹5000'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _quickChip(String label) {
    return GestureDetector(
      onTap: () {
        _controller.text = label.replaceAll(RegExp(r'^[^\s]+ '), '');
        _send();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          color: Colors.white.withValues(alpha: 0.06),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.7),
            fontSize: 13,
          ),
        ),
      ),
    );
  }

  Widget _buildMessageBubble(Map<String, String> m) {
    final isUser = m['role'] == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            // AI avatar
            Container(
              width: 28,
              height: 28,
              margin: const EdgeInsets.only(right: 8, bottom: 4),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF8B1538), Color(0xFF4A148C)],
                ),
                boxShadow: [
                  BoxShadow(
                    color:
                        const Color(0xFF8B1538).withValues(alpha: 0.3),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: const Icon(Icons.auto_awesome, size: 14, color: Colors.white),
            ),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              decoration:
                  isUser ? AuraTheme.userBubble : AuraTheme.assistantBubble,
              child: Text(
                m['text'] ?? '',
                style: TextStyle(
                  color: isUser ? Colors.white : Colors.white.withValues(alpha: 0.9),
                  fontSize: 14.5,
                  height: 1.4,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            margin: const EdgeInsets.only(right: 8),
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [Color(0xFF8B1538), Color(0xFF4A148C)],
              ),
            ),
            child: const Icon(Icons.auto_awesome, size: 14, color: Colors.white),
          ),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: AuraTheme.assistantBubble,
            child: AnimatedBuilder(
              animation: _typingCtrl,
              builder: (context, _) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(3, (i) {
                    final delay = i * 0.2;
                    final t = (_typingCtrl.value + delay) % 1.0;
                    final y = -4.0 * (t < 0.5 ? t : 1.0 - t);
                    return Transform.translate(
                      offset: Offset(0, y * 2),
                      child: Container(
                        width: 7,
                        height: 7,
                        margin: EdgeInsets.only(right: i < 2 ? 5 : 0),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: const Color(0xFFD4AF37)
                              .withValues(alpha: 0.4 + 0.4 * (1 - t)),
                        ),
                      ),
                    );
                  }),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
      decoration: BoxDecoration(
        color: const Color(0xFF121218).withValues(alpha: 0.9),
        border: Border(
          top: BorderSide(color: Colors.white.withValues(alpha: 0.06)),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            // Mic button with glow when listening
            Container(
              decoration: _isListening
                  ? BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.red.withValues(alpha: 0.4),
                          blurRadius: 12,
                          spreadRadius: 2,
                        ),
                      ],
                    )
                  : null,
              child: IconButton(
                icon: Icon(
                  _isListening ? Icons.mic : Icons.mic_outlined,
                  color: _isListening
                      ? Colors.red
                      : Colors.white.withValues(alpha: 0.5),
                  size: _isListening ? 28 : 24,
                ),
                onPressed: _toggleListening,
                tooltip: _isListening ? 'Stop listening' : 'Speak to AURA',
              ),
            ),
            const SizedBox(width: 4),
            Expanded(
              child: TextField(
                controller: _controller,
                style: const TextStyle(color: Colors.white, fontSize: 14.5),
                decoration: InputDecoration(
                  hintText: _isListening
                      ? 'Listening...'
                      : 'Ask about outfits, fabrics, styling…',
                ),
                onSubmitted: (_) => _send(),
              ),
            ),
            const SizedBox(width: 8),
            // Premium send button
            Container(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF8B1538), Color(0xFF6A0F2B)],
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF8B1538).withValues(alpha: 0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: IconButton(
                icon: const Icon(Icons.arrow_upward_rounded,
                    color: Colors.white, size: 20),
                onPressed: _send,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
