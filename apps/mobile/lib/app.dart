import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_i18n/flutter_i18n.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/aura_background.dart';
import 'core/api_provider.dart';
import 'features/auth/auth_screen.dart';
import 'features/home/home_screen.dart';

class FashionAiApp extends ConsumerWidget {
  const FashionAiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Force dark status bar icons on light background
    SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: Color(0xFFF5F9FF),
      systemNavigationBarIconBrightness: Brightness.dark,
    ));

    return MaterialApp(
      title: 'AURA Fashion AI',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.light,
      theme: AuraTheme.lightTheme,
      localizationsDelegates: [
        FlutterI18nDelegate(
          translationLoader: FileTranslationLoader(
            basePath: 'assets/i18n',
            fallbackFile: 'en',
            useCountryCode: false,
          ),
          missingTranslationHandler: (key, locale) {
            debugPrint('Missing translation: $key [$locale]');
          },
        ),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('en'),
        Locale('te'),
        Locale('hi'),
      ],
      home: const _AuthGate(),
    );
  }
}

/// Gates the app: shows AuthScreen until authenticated, then HomeScreen.
class _AuthGate extends ConsumerStatefulWidget {
  const _AuthGate();

  @override
  ConsumerState<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends ConsumerState<_AuthGate> {
  bool _ready = false;

  @override
  Widget build(BuildContext context) {
    // Try to restore cached session on first load
    final initAsync = ref.watch(initApiProvider);
    final isAuth = ref.watch(isAuthenticatedProvider);

    return initAsync.when(
      loading: () => const Scaffold(
        backgroundColor: Color(0xFFE3F2FD),
        body: Center(
          child: CircularProgressIndicator(
            color: Color(0xFF4A90E2),
          ),
        ),
      ),
      error: (_, __) => AuthScreen(
        onAuthenticated: () => setState(() => _ready = true),
      ),
      data: (restored) {
        if (restored || isAuth || _ready) {
          return const HomeScreen();
        }
        return AuthScreen(
          onAuthenticated: () => setState(() => _ready = true),
        );
      },
    );
  }
}

