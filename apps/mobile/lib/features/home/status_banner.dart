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

    // Only show banner when NOT online (keep UI clean when connected)
    if (connState == AppConnectionState.online) {
      return const SizedBox.shrink();
    }

    final (Color accent, String label, IconData icon, bool showSpinner) =
        switch (connState) {
      AppConnectionState.connecting => (
          const Color(0xFFD4AF37),
          'Connecting to AURA server…',
          Icons.sync,
          true,
        ),
      AppConnectionState.offline => (
          const Color(0xFFEF5350),
          'Offline — tap to reconnect',
          Icons.cloud_off_outlined,
          false,
        ),
      _ => (Colors.grey, '', Icons.info, false),
    };

    return GestureDetector(
      onTap: connState == AppConnectionState.offline
          ? () => ref.invalidate(initApiProvider)
          : null,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: accent.withValues(alpha: 0.1),
          border: Border(
            bottom: BorderSide(color: accent.withValues(alpha: 0.2)),
          ),
        ),
        child: SafeArea(
          bottom: false,
          child: Row(
            children: [
              Icon(icon, color: accent, size: 16),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    color: accent,
                    fontWeight: FontWeight.w500,
                    fontSize: 12,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
              if (showSpinner)
                SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 1.5,
                    color: accent,
                  ),
                ),
              if (connState == AppConnectionState.offline)
                Icon(Icons.refresh, color: accent, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}
