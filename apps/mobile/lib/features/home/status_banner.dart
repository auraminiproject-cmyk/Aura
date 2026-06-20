import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_provider.dart';

class StatusBanner extends ConsumerWidget {
  const StatusBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Trigger the initial connection attempt
    ref.watch(initApiProvider);
    final connState = ref.watch(connectionStateProvider);

    final (Color bg, Color fg, String label, IconData icon) = switch (connState) {
      AppConnectionState.online => (
          const Color(0xFF1B5E20),
          Colors.white,
          'Online — Fashion AI ready',
          Icons.cloud_done,
        ),
      AppConnectionState.connecting => (
          const Color(0xFFF57F17),
          Colors.black87,
          'Connecting to server…',
          Icons.sync,
        ),
      AppConnectionState.offline => (
          const Color(0xFFB71C1C),
          Colors.white,
          'Offline — tap to retry',
          Icons.cloud_off,
        ),
    };

    return GestureDetector(
      onTap: connState == AppConnectionState.offline
          ? () => ref.invalidate(initApiProvider)
          : null,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: bg,
          boxShadow: [
            BoxShadow(
              color: bg.withValues(alpha: 0.3),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: SafeArea(
          bottom: false,
          child: Row(
            children: [
              Icon(icon, color: fg, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(color: fg, fontWeight: FontWeight.w500, fontSize: 13),
                ),
              ),
              if (connState == AppConnectionState.connecting)
                SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: fg,
                  ),
                ),
              if (connState == AppConnectionState.offline)
                Icon(Icons.refresh, color: fg, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}
