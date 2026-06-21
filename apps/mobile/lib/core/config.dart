class AppConfig {
  /// API base URL — defaults to Render production.
  /// Override for local dev: flutter build apk --dart-define=API_BASE_URL=http://10.0.2.2:8000
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://aura1-3rk2.onrender.com',
  );
}
