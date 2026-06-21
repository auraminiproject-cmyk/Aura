import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'config.dart';

/// Tracks whether we are online (authenticated with backend) or offline.
final connectionStateProvider = StateProvider<AppConnectionState>(
  (_) => AppConnectionState.connecting,
);

enum AppConnectionState { connecting, online, offline }

/// The API client – always available (never throws).
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(baseUrl: AppConfig.apiBaseUrl);
});

/// Attempts to connect. First tries guest login; if the endpoint doesn't
/// exist (404), falls back to health check to confirm the server is reachable.
final initApiProvider = FutureProvider<void>((ref) async {
  final client = ref.read(apiClientProvider);
  final connState = ref.read(connectionStateProvider.notifier);
  connState.state = AppConnectionState.connecting;

  try {
    // Try guest login first (full auth flow)
    await client.guestLogin();
    connState.state = AppConnectionState.online;
  } catch (_) {
    // If guest login fails (404, 500, etc.), try health check
    try {
      await client.healthCheck();
      connState.state = AppConnectionState.online;
    } catch (_) {
      connState.state = AppConnectionState.offline;
    }
  }
});
