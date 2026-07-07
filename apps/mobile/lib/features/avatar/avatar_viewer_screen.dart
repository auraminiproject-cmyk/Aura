import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class AvatarViewerScreen extends StatelessWidget {
  const AvatarViewerScreen({super.key, this.glbUrl});

  final String? glbUrl;

  @override
  Widget build(BuildContext context) {
    final src =
        glbUrl ?? 'https://modelviewer.dev/shared-assets/models/Astronaut.glb';
    return Scaffold(
      appBar: AppBar(title: const Text('3D Avatar')),
      body: ModelViewer(
        src: src,
        alt: 'Fashion AI Avatar',
        ar: false,
        autoRotate: true,
        cameraControls: true,
        backgroundColor: const Color(0xFF1a1a2e),
      ),
    );
  }
}
