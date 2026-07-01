import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_provider.dart';

class AvatarCaptureScreen extends ConsumerStatefulWidget {
  const AvatarCaptureScreen({super.key});

  @override
  ConsumerState<AvatarCaptureScreen> createState() => _AvatarCaptureScreenState();
}

class _AvatarCaptureScreenState extends ConsumerState<AvatarCaptureScreen> {
  final _picker = ImagePicker();
  final _heightController = TextEditingController(text: '165');
  String? _frontPath;
  String? _sidePath;
  bool _uploading = false;
  String _statusText = '';
  Map<String, dynamic>? _result;

  Future<void> _pick(bool front) async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: const Color(0xFF1A1A2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40, height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.camera_alt, color: Color(0xFFD4AF37)),
                title: const Text('Take Photo', style: TextStyle(color: Colors.white)),
                subtitle: Text(
                  'Use camera for best results',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
                ),
                onTap: () => Navigator.pop(ctx, ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: Color(0xFFD4AF37)),
                title: const Text('Choose from Gallery', style: TextStyle(color: Colors.white)),
                subtitle: Text(
                  'Select an existing full-body photo',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
                ),
                onTap: () => Navigator.pop(ctx, ImageSource.gallery),
              ),
            ],
          ),
        ),
      ),
    );
    if (source == null) return;

    try {
      final file = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        imageQuality: 90,
      );
      if (file == null) return;
      setState(() {
        if (front) {
          _frontPath = file.path;
        } else {
          _sidePath = file.path;
        }
        _result = null; // Clear previous results
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(
            e.toString().contains('denied') || e.toString().contains('permission')
                ? '📷 Camera permission denied. Enable it in Settings.'
                : 'Error: $e',
          )),
        );
      }
    }
  }

  Future<void> _analyze() async {
    if (_frontPath == null) return;
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⚠️ Cannot analyze while offline')),
      );
      return;
    }

    final heightCm = double.tryParse(_heightController.text) ?? 165.0;
    if (heightCm < 100 || heightCm > 250) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('⚠️ Enter height between 100–250 cm')),
      );
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() {
      _uploading = true;
      _statusText = 'Uploading photo...';
      _result = null;
    });

    try {
      setState(() => _statusText = 'Analyzing body proportions...');
      final resp = await api.analyzeBody(
        frontPath: _frontPath!,
        sidePath: _sidePath,
        heightCm: heightCm,
      );
      setState(() {
        _result = resp;
        _statusText = '';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Body analysis complete!'),
            backgroundColor: Color(0xFF2E7D32),
          ),
        );
      }
    } catch (e) {
      setState(() => _statusText = '');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Analysis failed: $e'),
            backgroundColor: Colors.red.shade800,
          ),
        );
      }
    } finally {
      setState(() => _uploading = false);
    }
  }

  @override
  void dispose() {
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final measurements = _result?['measurements'] as Map<String, dynamic>?;
    final confidence = (_result?['confidence'] as num?)?.toDouble();

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('Body Analysis'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Header
          _buildHeader(),
          const SizedBox(height: 24),

          // Photo capture cards
          Row(
            children: [
              Expanded(
                child: _PhotoCard(
                  label: 'Front Photo',
                  sublabel: 'Required',
                  icon: Icons.person,
                  imagePath: _frontPath,
                  required: true,
                  onTap: () => _pick(true),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _PhotoCard(
                  label: 'Side Photo',
                  sublabel: 'Optional',
                  icon: Icons.person_outline,
                  imagePath: _sidePath,
                  required: false,
                  onTap: () => _pick(false),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Height input
          _buildHeightInput(),
          const SizedBox(height: 20),

          // Analyze button
          _buildAnalyzeButton(),

          // Status text
          if (_statusText.isNotEmpty) ...[
            const SizedBox(height: 12),
            Center(
              child: Text(
                _statusText,
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.7),
                  fontSize: 13,
                ),
              ),
            ),
          ],

          // Results
          if (measurements != null) ...[
            const SizedBox(height: 24),
            _buildResultsCard(measurements, confidence),
          ],
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        Container(
          width: 64, height: 64,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              colors: [Color(0xFF8B1538), Color(0xFF4A148C)],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF8B1538).withValues(alpha: 0.4),
                blurRadius: 20,
              ),
            ],
          ),
          child: const Icon(Icons.straighten, color: Colors.white, size: 28),
        ),
        const SizedBox(height: 12),
        const Text(
          'AI Body Measurement',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Take a full-body photo to extract your\nmeasurements for perfect outfit fitting',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.6),
            fontSize: 13,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildHeightInput() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.height, color: Color(0xFFD4AF37), size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Your Height',
                  style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                ),
                Text(
                  'Required for accurate measurements',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 11),
                ),
              ],
            ),
          ),
          SizedBox(
            width: 80,
            child: TextField(
              controller: _heightController,
              keyboardType: TextInputType.number,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
              decoration: InputDecoration(
                suffixText: 'cm',
                suffixStyle: TextStyle(
                  color: Colors.white.withValues(alpha: 0.5),
                  fontSize: 12,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFFD4AF37)),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalyzeButton() {
    return Container(
      width: double.infinity,
      height: 52,
      decoration: BoxDecoration(
        gradient: _frontPath != null && !_uploading
            ? const LinearGradient(colors: [Color(0xFF8B1538), Color(0xFF6A0F2B)])
            : null,
        color: _frontPath == null || _uploading ? Colors.grey.shade800 : null,
        borderRadius: BorderRadius.circular(16),
        boxShadow: _frontPath != null && !_uploading
            ? [
                BoxShadow(
                  color: const Color(0xFF8B1538).withValues(alpha: 0.4),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _frontPath == null || _uploading ? null : _analyze,
          borderRadius: BorderRadius.circular(16),
          child: Center(
            child: _uploading
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(
                        width: 18, height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        _statusText.isNotEmpty ? _statusText : 'Analyzing...',
                        style: const TextStyle(color: Colors.white, fontSize: 15),
                      ),
                    ],
                  )
                : const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.analytics, color: Colors.white, size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Analyze Body Measurements',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildResultsCard(Map<String, dynamic> measurements, double? confidence) {
    final confidencePct = ((confidence ?? 0.5) * 100).toInt();
    final isHighConf = confidencePct >= 70;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.white.withValues(alpha: 0.08),
            Colors.white.withValues(alpha: 0.03),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isHighConf
              ? const Color(0xFFD4AF37).withValues(alpha: 0.3)
              : Colors.white.withValues(alpha: 0.1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isHighConf
                      ? const Color(0xFF2E7D32).withValues(alpha: 0.2)
                      : const Color(0xFFE65100).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  isHighConf ? Icons.verified : Icons.info_outline,
                  color: isHighConf ? Colors.green.shade300 : Colors.orange.shade300,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Your Measurements',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Confidence: $confidencePct%${isHighConf ? " • AI Verified" : " • Estimated"}',
                      style: TextStyle(
                        color: isHighConf ? Colors.green.shade300 : Colors.orange.shade300,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Confidence bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (confidence ?? 0.5),
              backgroundColor: Colors.white.withValues(alpha: 0.1),
              valueColor: AlwaysStoppedAnimation(
                isHighConf ? Colors.green.shade400 : Colors.orange.shade400,
              ),
              minHeight: 4,
            ),
          ),
          const SizedBox(height: 20),
          // Measurement grid
          _MeasurementGrid(measurements: measurements),
        ],
      ),
    );
  }
}

class _MeasurementGrid extends StatelessWidget {
  const _MeasurementGrid({required this.measurements});
  final Map<String, dynamic> measurements;

  @override
  Widget build(BuildContext context) {
    final items = <MapEntry<String, String>>[];

    void add(String key, String label, String unit) {
      final val = measurements[key];
      if (val != null) items.add(MapEntry(label, '${val} $unit'));
    }

    add('height_cm', 'Height', 'cm');
    add('shoulder_cm', 'Shoulder', 'cm');
    add('chest_cm', 'Chest', 'cm');
    add('waist_cm', 'Waist', 'cm');
    add('hip_cm', 'Hip', 'cm');
    add('inseam_cm', 'Inseam', 'cm');
    add('arm_length_cm', 'Arm Length', 'cm');
    add('torso_length_cm', 'Torso', 'cm');
    add('neck_cm', 'Neck', 'cm');

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 1.3,
        crossAxisSpacing: 10,
        mainAxisSpacing: 10,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                item.value,
                style: const TextStyle(
                  color: Color(0xFFD4AF37),
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                item.key,
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.6),
                  fontSize: 11,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      },
    );
  }
}

class _PhotoCard extends StatelessWidget {
  const _PhotoCard({
    required this.label,
    required this.sublabel,
    required this.icon,
    required this.imagePath,
    required this.required,
    required this.onTap,
  });

  final String label;
  final String sublabel;
  final IconData icon;
  final String? imagePath;
  final bool required;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: imagePath != null
                ? const Color(0xFFD4AF37).withValues(alpha: 0.5)
                : Colors.white.withValues(alpha: 0.1),
            width: imagePath != null ? 2 : 1,
          ),
          color: Colors.white.withValues(alpha: 0.04),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(15),
          child: imagePath != null
              ? Stack(
                  fit: StackFit.expand,
                  children: [
                    Image.file(
                      File(imagePath!),
                      fit: BoxFit.cover,
                    ),
                    // Gradient overlay
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.7),
                          ],
                        ),
                      ),
                    ),
                    // Label at bottom
                    Positioned(
                      bottom: 10,
                      left: 10,
                      right: 10,
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle, color: Color(0xFFD4AF37), size: 16),
                          const SizedBox(width: 6),
                          Text(
                            label,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Re-take button
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.refresh, color: Colors.white, size: 16),
                      ),
                    ),
                  ],
                )
              : Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(icon, size: 40, color: Colors.white.withValues(alpha: 0.3)),
                    const SizedBox(height: 10),
                    Text(
                      label,
                      style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        color: required
                            ? const Color(0xFF8B1538).withValues(alpha: 0.3)
                            : Colors.white.withValues(alpha: 0.05),
                      ),
                      child: Text(
                        sublabel,
                        style: TextStyle(
                          color: required
                              ? Colors.red.shade200
                              : Colors.white.withValues(alpha: 0.4),
                          fontSize: 10,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Icon(Icons.add_a_photo, size: 18, color: Colors.white.withValues(alpha: 0.3)),
                  ],
                ),
        ),
      ),
    );
  }
}
