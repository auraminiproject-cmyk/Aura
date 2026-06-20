import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'config.dart';

/// Tracks whether we are online (authenticated with backend) or offline.
final connectionStateProvider = StateProvider<AppConnectionState>(
  (_) => AppConnectionState.connecting,
);

enum AppConnectionState { connecting, online, offline }

/// The API client – always available (never throws).
/// If guestLogin fails, the client is still usable for offline-tolerant UI;
/// individual calls will fail gracefully.
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(baseUrl: AppConfig.apiBaseUrl);
});

/// Attempts guest login. Called once on app start; can be retried.
final initApiProvider = FutureProvider<void>((ref) async {
  final client = ref.read(apiClientProvider);
  final connState = ref.read(connectionStateProvider.notifier);
  connState.state = AppConnectionState.connecting;

  try {
    await client.guestLogin();
    connState.state = AppConnectionState.online;
  } catch (_) {
    connState.state = AppConnectionState.offline;
  }
});
