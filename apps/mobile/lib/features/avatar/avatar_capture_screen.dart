import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_provider.dart';
import 'avatar_viewer_screen.dart';

class AvatarCaptureScreen extends ConsumerStatefulWidget {
  const AvatarCaptureScreen({super.key});

  @override
  ConsumerState<AvatarCaptureScreen> createState() => _AvatarCaptureScreenState();
}

class _AvatarCaptureScreenState extends ConsumerState<AvatarCaptureScreen> {
  final _picker = ImagePicker();
  String? _frontPath;
  String? _sidePath;
  bool _uploading = false;
  Map<String, dynamic>? _result;

  Future<void> _pick(bool front) async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Camera'),
              onTap: () => Navigator.pop(ctx, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Gallery'),
              onTap: () => Navigator.pop(ctx, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source == null) return;

    try {
      final file = await _picker.pickImage(
        source: source,
        maxWidth: 800,
        imageQuality: 85,
      );
      if (file == null) return;
      setState(() {
        if (front) {
          _frontPath = file.path;
        } else {
          _sidePath = file.path;
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(
            e.toString().contains('denied') || e.toString().contains('permission')
                ? '📷 Camera permission denied. Please enable it in Settings.'
                : 'Error: $e',
          )),
        );
      }
    }
  }

  Future<void> _upload() async {
    if (_frontPath == null) return;
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⚠️ Cannot upload while offline')),
      );
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() => _uploading = true);
    try {
      final resp = await api.uploadAvatar(frontPath: _frontPath!, sidePath: _sidePath);
      setState(() => _result = resp);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ Avatar reconstructed successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Upload failed: $e')));
      }
    } finally {
      setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Avatar Capture')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Icon(Icons.face_retouching_natural, size: 64, color: Color(0xFF8B1538)),
            const SizedBox(height: 12),
            const Text(
              'Capture or select photos for your 3D avatar',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Front photo is required. Side photo improves accuracy.',
              style: TextStyle(color: Colors.grey.shade600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _PhotoButton(
                  label: 'Front',
                  icon: Icons.camera_front,
                  selected: _frontPath != null,
                  onTap: () => _pick(true),
                ),
                _PhotoButton(
                  label: 'Side (optional)',
                  icon: Icons.camera_rear,
                  selected: _sidePath != null,
                  onTap: () => _pick(false),
                ),
              ],
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _frontPath == null || _uploading ? null : _upload,
              icon: _uploading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.upload),
              label: Text(_uploading ? 'Uploading...' : 'Upload & Reconstruct'),
            ),
            if (_result != null) ...[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    children: [
                      Text('Confidence: ${_result!['confidence']}',
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                      Text('Measurements: ${_result!['measurements']}'),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const AvatarViewerScreen()),
                        ),
                        icon: const Icon(Icons.view_in_ar),
                        label: const Text('View 3D Avatar'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PhotoButton extends StatelessWidget {
  const _PhotoButton({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: 140,
        height: 140,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected ? Theme.of(context).colorScheme.primary : Colors.grey.shade300,
            width: selected ? 2 : 1,
          ),
          color: selected
              ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3)
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              selected ? Icons.check_circle : icon,
              size: 40,
              color: selected ? Theme.of(context).colorScheme.primary : Colors.grey,
            ),
            const SizedBox(height: 8),
            Text(
              selected ? '$label ✓' : label,
              style: TextStyle(
                color: selected ? Theme.of(context).colorScheme.primary : null,
                fontWeight: selected ? FontWeight.bold : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
