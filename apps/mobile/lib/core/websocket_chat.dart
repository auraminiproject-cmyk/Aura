import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'config.dart';

class WebSocketChat {
  WebSocketChannel? _channel;

  void connect(String sessionId) {
    final base = AppConfig.apiBaseUrl.replaceFirst('http', 'ws');
    _channel = WebSocketChannel.connect(Uri.parse('$base/api/v1/chat/ws/$sessionId'));
  }

  Stream<dynamic> get stream => _channel!.stream;

  void sendText(String message, {String language = 'te'}) {
    _channel?.sink.add(jsonEncode({'message': message, 'language': language}));
  }

  void dispose() => _channel?.sink.close();
}
