import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_i18n/flutter_i18n.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/aura_background.dart';
import 'features/chat/chat_screen.dart';
import 'features/home/status_banner.dart';
import 'features/avatar/avatar_capture_screen.dart';
import 'features/design/design_screen.dart';
import 'features/products/product_results_screen.dart';
import 'features/wardrobe/wardrobe_screen.dart';

class FashionAiApp extends ConsumerWidget {
  const FashionAiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Force dark status bar icons on dark background
    SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF121218),
      systemNavigationBarIconBrightness: Brightness.light,
    ));

    return MaterialApp(
      title: 'AURA Fashion AI',
      debugShowCheckedModeBanner: false,
      theme: AuraTheme.darkTheme,
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
      home: const MainShell(),
    );
  }
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  static const _tabs = [
    ('Chat', Icons.auto_awesome, Icons.auto_awesome_outlined),
    ('Avatar', Icons.face_retouching_natural, Icons.face_retouching_natural_outlined),
    ('Design', Icons.brush, Icons.brush_outlined),
    ('Shop', Icons.shopping_bag, Icons.shopping_bag_outlined),
    ('Wardrobe', Icons.checkroom, Icons.checkroom_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    final screens = [
      const ChatScreen(),
      const AvatarCaptureScreen(),
      const DesignScreen(),
      const ProductResultsScreen(),
      const WardrobeScreen(),
    ];

    return AuraBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: Column(
          children: [
            const StatusBanner(),
            Expanded(child: screens[_index]),
          ],
        ),
        bottomNavigationBar: Container(
          decoration: BoxDecoration(
            border: Border(
              top: BorderSide(
                color: Colors.white.withValues(alpha: 0.06),
              ),
            ),
          ),
          child: NavigationBar(
            selectedIndex: _index,
            onDestinationSelected: (i) => setState(() => _index = i),
            destinations: [
              for (final t in _tabs)
                NavigationDestination(
                  icon: Icon(t.$3),
                  selectedIcon: Icon(t.$2),
                  label: t.$1,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
