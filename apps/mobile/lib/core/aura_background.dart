import 'dart:math';
import 'package:flutter/material.dart';

/// Premium animated wired/mesh background with floating particles.
/// Creates a light icy blue futuristic aesthetic with glowing connection lines.
class AuraBackground extends StatefulWidget {
  final Widget child;
  final bool showMesh;

  const AuraBackground({
    super.key,
    required this.child,
    this.showMesh = true,
  });

  @override
  State<AuraBackground> createState() => _AuraBackgroundState();
}

class _AuraBackgroundState extends State<AuraBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 20),
    )..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Base gradient
        Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF42A5F5), // Light blue
                Color(0xFF2196F3), // Vibrant blue
                Color(0xFF1E88E5), // Deeper blue
                Color(0xFF42A5F5), // Back to light blue
              ],
              stops: [0.0, 0.35, 0.7, 1.0],
            ),
          ),
        ),
        // Animated mesh overlay
        if (widget.showMesh)
          AnimatedBuilder(
            animation: _ctrl,
            builder: (context, _) {
              return CustomPaint(
                size: MediaQuery.of(context).size,
                painter: _WireMeshPainter(
                  progress: _ctrl.value,
                ),
              );
            },
          ),
        // Radial glow spots
        Positioned(
          top: -80,
          right: -60,
          child: _GlowOrb(
            color: const Color(0xFF64B5F6),
            size: 280,
            controller: _ctrl,
            offset: 0.0,
          ),
        ),
        Positioned(
          bottom: -100,
          left: -80,
          child: _GlowOrb(
            color: const Color(0xFF2196F3),
            size: 320,
            controller: _ctrl,
            offset: 0.5,
          ),
        ),
        Positioned(
          top: MediaQuery.of(context).size.height * 0.4,
          right: -40,
          child: _GlowOrb(
            color: const Color(0xFF1976D2),
            size: 200,
            controller: _ctrl,
            offset: 0.3,
          ),
        ),
        // Content
        widget.child,
      ],
    );
  }
}

class _GlowOrb extends StatelessWidget {
  final Color color;
  final double size;
  final AnimationController controller;
  final double offset;

  const _GlowOrb({
    required this.color,
    required this.size,
    required this.controller,
    required this.offset,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, child) {
        final t = (controller.value + offset) % 1.0;
        final pulse = 0.3 + 0.7 * (0.5 + 0.5 * sin(t * 2 * pi));
        return Opacity(
          opacity: 0.15 * pulse,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  color,
                  color.withValues(alpha: 0.0),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _WireMeshPainter extends CustomPainter {
  final double progress;
  static final List<_MeshNode> _nodes = _generateNodes(35);

  _WireMeshPainter({required this.progress});

  static List<_MeshNode> _generateNodes(int count) {
    final rng = Random(42); // Fixed seed for consistent mesh
    return List.generate(count, (i) {
      return _MeshNode(
        baseX: rng.nextDouble(),
        baseY: rng.nextDouble(),
        speedX: (rng.nextDouble() - 0.5) * 0.02,
        speedY: (rng.nextDouble() - 0.5) * 0.015,
        phase: rng.nextDouble() * 2 * pi,
        radius: 1.5 + rng.nextDouble() * 2.0,
      );
    });
  }

  @override
  void paint(Canvas canvas, Size size) {
    final nodePaint = Paint()..style = PaintingStyle.fill;
    final linePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.5;

    final positions = <Offset>[];

    // Calculate animated positions
    for (final node in _nodes) {
      final t = progress * 2 * pi;
      final x = (node.baseX + sin(t + node.phase) * node.speedX) * size.width;
      final y =
          (node.baseY + cos(t * 0.7 + node.phase) * node.speedY) * size.height;
      positions.add(Offset(x.clamp(0, size.width), y.clamp(0, size.height)));
    }

    // Draw connection lines between nearby nodes
    const maxDist = 150.0;
    for (var i = 0; i < positions.length; i++) {
      for (var j = i + 1; j < positions.length; j++) {
        final dist = (positions[i] - positions[j]).distance;
        if (dist < maxDist) {
          final alpha = (1.0 - dist / maxDist) * 0.2;
          linePaint.color = Color.fromRGBO(74, 144, 226, alpha); // Brand Blue
          canvas.drawLine(positions[i], positions[j], linePaint);
        }
      }
    }

    // Draw nodes
    for (var i = 0; i < positions.length; i++) {
      final glowAlpha = 0.3 + 0.3 * sin(progress * 2 * pi + _nodes[i].phase);
      nodePaint.color = Color.fromRGBO(100, 181, 246, glowAlpha);
      canvas.drawCircle(positions[i], _nodes[i].radius, nodePaint);
      // Inner bright point
      nodePaint.color = Color.fromRGBO(255, 255, 255, glowAlpha * 0.8);
      canvas.drawCircle(positions[i], _nodes[i].radius * 0.4, nodePaint);
    }
  }

  @override
  bool shouldRepaint(covariant _WireMeshPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _MeshNode {
  final double baseX, baseY, speedX, speedY, phase, radius;
  const _MeshNode({
    required this.baseX,
    required this.baseY,
    required this.speedX,
    required this.speedY,
    required this.phase,
    required this.radius,
  });
}

/// Premium light theme for the entire app
class AuraTheme {
  static const _brandBlue = Color(0xFF1976D2);
  static const _surfaceLight = Color(0xFF64B5F6);
  static const _surfaceCard = Color(0xFF42A5F5);
  static const _textPrimary = Colors.white;
  static const _textSecondary = Colors.white70;

  static const _surfaceDark = Color(0xFF0F172A);
  static const _surfaceCardDark = Color(0xFF1E293B);
  static const _textPrimaryDark = Color(0xFFF1F5F9);
  static const _textSecondaryDark = Color(0xFF94A3B8);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.transparent,
      colorScheme: ColorScheme.dark(
        primary: _brandBlue,
        secondary: _brandBlue,
        surface: _surfaceDark,
        onSurface: _textPrimaryDark,
        onPrimary: Colors.white,
        primaryContainer: _brandBlue.withValues(alpha: 0.2),
        secondaryContainer: _brandBlue.withValues(alpha: 0.1),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.bold,
            color: _textPrimaryDark),
        displayMedium: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.bold,
            color: _textPrimaryDark),
        displaySmall: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.bold,
            color: _textPrimaryDark),
        headlineLarge: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w700,
            color: _textPrimaryDark),
        headlineMedium: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w600,
            color: _textPrimaryDark),
        headlineSmall: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w600,
            color: _textPrimaryDark),
        titleLarge: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w600,
            color: _textPrimaryDark),
        titleMedium: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w500,
            color: _textPrimaryDark),
        titleSmall: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w500,
            color: _textPrimaryDark),
        bodyLarge: TextStyle(fontFamily: 'Outfit', color: _textSecondaryDark),
        bodyMedium: TextStyle(fontFamily: 'Outfit', color: _textSecondaryDark),
        bodySmall: TextStyle(fontFamily: 'Outfit', color: _textSecondaryDark),
        labelLarge: TextStyle(
            fontFamily: 'Outfit',
            fontWeight: FontWeight.w600,
            color: _textPrimaryDark),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: const TextStyle(
          fontFamily: 'Outfit',
          fontWeight: FontWeight.w600,
          fontSize: 20,
          color: _textPrimaryDark,
        ),
        iconTheme:
            IconThemeData(color: _textPrimaryDark.withValues(alpha: 0.8)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: _surfaceDark.withValues(alpha: 0.9),
        indicatorColor: _brandBlue.withValues(alpha: 0.2),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
                fontFamily: 'Outfit',
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: _brandBlue);
          }
          return TextStyle(
              fontFamily: 'Outfit',
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: _textSecondaryDark.withValues(alpha: 0.8));
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: _brandBlue, size: 24);
          }
          return IconThemeData(
              color: _textSecondaryDark.withValues(alpha: 0.6), size: 22);
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _surfaceCardDark,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: _brandBlue.withValues(alpha: 0.1)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: _brandBlue.withValues(alpha: 0.1)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: _brandBlue, width: 2),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        labelStyle: TextStyle(color: _textSecondaryDark.withValues(alpha: 0.8)),
        hintStyle: TextStyle(color: _textSecondaryDark.withValues(alpha: 0.5)),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          foregroundColor: _brandBlue,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: _brandBlue,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(
              fontFamily: 'Outfit', fontSize: 16, fontWeight: FontWeight.bold),
        ),
      ),
      cardTheme: CardThemeData(
        color: _surfaceCardDark,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: _brandBlue.withValues(alpha: 0.05)),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: _brandBlue.withValues(alpha: 0.05),
        thickness: 1,
        space: 24,
      ),
    );
  }

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: Colors.transparent,
      colorScheme: ColorScheme.light(
        primary: _brandBlue,
        secondary: _brandBlue,
        surface: _surfaceLight,
        onSurface: _textPrimary,
        onPrimary: Colors.white,
        primaryContainer: _brandBlue.withValues(alpha: 0.1),
        secondaryContainer: _brandBlue.withValues(alpha: 0.05),
        outline: _brandBlue.withValues(alpha: 0.2),
      ),
      fontFamily: 'Roboto',
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          color: _textPrimary,
          fontWeight: FontWeight.w700,
          fontSize: 28,
          letterSpacing: -0.5,
        ),
        headlineMedium: TextStyle(
          color: _textPrimary,
          fontWeight: FontWeight.w600,
          fontSize: 22,
        ),
        titleMedium: TextStyle(
          color: _textPrimary,
          fontWeight: FontWeight.w500,
          fontSize: 16,
        ),
        bodyLarge: TextStyle(color: _textPrimary, fontSize: 15),
        bodyMedium: TextStyle(color: _textSecondary, fontSize: 14),
        labelLarge: TextStyle(
          color: _textPrimary,
          fontWeight: FontWeight.w600,
          fontSize: 14,
          letterSpacing: 0.5,
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: const TextStyle(
          color: _textPrimary,
          fontWeight: FontWeight.w600,
          fontSize: 18,
          letterSpacing: 0.3,
        ),
        iconTheme: IconThemeData(color: _textPrimary.withValues(alpha: 0.8)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: _surfaceCard.withValues(alpha: 0.95),
        indicatorColor: _brandBlue.withValues(alpha: 0.15),
        labelTextStyle: const WidgetStatePropertyAll(
          TextStyle(
              fontSize: 11, color: _textSecondary, fontWeight: FontWeight.w500),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: _brandBlue, size: 24);
          }
          return IconThemeData(
              color: _textSecondary.withValues(alpha: 0.6), size: 22);
        }),
        elevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _surfaceCard.withValues(alpha: 0.8),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: _brandBlue.withValues(alpha: 0.2)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: _brandBlue.withValues(alpha: 0.2)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: _brandBlue, width: 1.5),
        ),
        hintStyle: TextStyle(
            color: _textSecondary.withValues(alpha: 0.5), fontSize: 14),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: ButtonStyle(
          foregroundColor:
              WidgetStatePropertyAll(_textPrimary.withValues(alpha: 0.8)),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: ButtonStyle(
          backgroundColor: const WidgetStatePropertyAll(_brandBlue),
          foregroundColor: const WidgetStatePropertyAll(Colors.white),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: _surfaceCard.withValues(alpha: 0.9),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: _brandBlue.withValues(alpha: 0.1)),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: _brandBlue.withValues(alpha: 0.1),
      ),
    );
  }

  // Glassmorphic card decoration
  static BoxDecoration glassCard(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return BoxDecoration(
      color: (isDark ? _surfaceCardDark : _surfaceCard).withValues(alpha: 0.85),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(
        color: _brandBlue.withValues(alpha: 0.15),
      ),
      boxShadow: [
        BoxShadow(
          color: _brandBlue.withValues(alpha: 0.05),
          blurRadius: 20,
          offset: const Offset(0, 8),
        ),
      ],
    );
  }

  // Gradient for chat bubbles (assistant)
  static BoxDecoration assistantBubble(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardColor = isDark ? _surfaceCardDark : _surfaceCard;
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          cardColor.withValues(alpha: 0.9),
          cardColor,
        ],
      ),
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(20),
        topRight: Radius.circular(20),
        bottomLeft: Radius.circular(4),
        bottomRight: Radius.circular(20),
      ),
      border: Border.all(
        color: _brandBlue.withValues(alpha: 0.15),
      ),
      boxShadow: [
        BoxShadow(
          color: _brandBlue.withValues(alpha: 0.05),
          blurRadius: 8,
          offset: const Offset(0, 4),
        ),
      ],
    );
  }

  // Gradient for chat bubbles (user)
  static BoxDecoration userBubble(BuildContext context) => BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF4A90E2),
            Color(0xFF1976D2),
          ],
        ),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
          bottomLeft: Radius.circular(20),
          bottomRight: Radius.circular(4),
        ),
        boxShadow: [
          BoxShadow(
            color: _brandBlue.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      );
}
