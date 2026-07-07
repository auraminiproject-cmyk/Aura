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
                Color(0xFFE3F2FD),  // Light icy blue
                Color(0xFFBBDEFB),  // Soft blue
                Color(0xFF90CAF9),  // Light blue
                Color(0xFFE3F2FD),  // Back to light blue
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
      final y = (node.baseY + cos(t * 0.7 + node.phase) * node.speedY) * size.height;
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
  static const _brandBlue = Color(0xFF4A90E2);
  static const _surfaceLight = Color(0xFFF5F9FF);
  static const _surfaceCard = Color(0xFFFFFFFF);
  static const _textPrimary = Color(0xFF1A237E);
  static const _textSecondary = Color(0xFF5C6BC0);

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
          TextStyle(fontSize: 11, color: _textSecondary, fontWeight: FontWeight.w500),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: _brandBlue, size: 24);
          }
          return IconThemeData(color: _textSecondary.withValues(alpha: 0.6), size: 22);
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
        hintStyle: TextStyle(color: _textSecondary.withValues(alpha: 0.5), fontSize: 14),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: ButtonStyle(
          foregroundColor: WidgetStatePropertyAll(_textPrimary.withValues(alpha: 0.8)),
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
  static BoxDecoration get glassCard => BoxDecoration(
        color: _surfaceCard.withValues(alpha: 0.85),
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

  // Gradient for chat bubbles (assistant)
  static BoxDecoration get assistantBubble => BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            _surfaceCard.withValues(alpha: 0.9),
            _surfaceCard,
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

  // Gradient for chat bubbles (user)
  static BoxDecoration get userBubble => BoxDecoration(
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
