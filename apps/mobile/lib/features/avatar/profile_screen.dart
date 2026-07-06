import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_provider.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _picker = ImagePicker();
  final _heightController = TextEditingController(text: '165');
  bool _isRetaking = false;

  // Photo state
  String? _frontPath;
  String? _sidePath;
  Map<String, dynamic>? _frontQuality;
  Map<String, dynamic>? _sideQuality;

  // Analysis state
  bool _analyzing = false;
  String _statusText = '';
  Map<String, dynamic>? _result;

  // Stored measurements
  Map<String, dynamic>? _storedMeasurements;

  @override
  void initState() {
    super.initState();
    _loadStoredMeasurements();
  }

  Future<void> _loadStoredMeasurements() async {
    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.getMeasurements();
      if (resp['has_profile'] == true) {
        setState(() => _storedMeasurements = resp);
      }
    } catch (_) {
      // No stored measurements
    }
  }

  Future<void> _pickAndValidate(bool isFront) async {
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
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.camera_alt, color: Color(0xFFD4AF37)),
                title: const Text('Take Photo', style: TextStyle(color: Colors.white)),
                subtitle: Text(isFront ? 'Stand facing the camera, arms slightly away' : 'Turn 90° to your left or right', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
                onTap: () => Navigator.pop(ctx, ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: Color(0xFFD4AF37)),
                title: const Text('Choose from Gallery', style: TextStyle(color: Colors.white)),
                onTap: () => Navigator.pop(ctx, ImageSource.gallery),
              ),
            ],
          ),
        ),
      ),
    );
    if (source == null) return;

    try {
      final file = await _picker.pickImage(source: source, maxWidth: 1024, imageQuality: 90);
      if (file == null) return;

      setState(() {
        if (isFront) {
          _frontPath = file.path;
          _frontQuality = null;
        } else {
          _sidePath = file.path;
          _sideQuality = null;
        }
        _result = null;
      });

      // Auto-check quality
      await _checkQuality(file.path, isFront);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('📷 ${e.toString().contains("permission") ? "Camera permission denied" : "Error: $e"}')),
        );
      }
    }
  }

  Future<void> _checkQuality(String path, bool isFront) async {
    final connState = ref.read(connectionStateProvider);
    if (connState != AppConnectionState.online) return;

    try {
      final api = ref.read(apiClientProvider);
      final quality = await api.checkImageQuality(path);
      setState(() {
        if (isFront) {
          _frontQuality = quality;
        } else {
          _sideQuality = quality;
        }
      });

      // Show warning if quality is poor
      if (quality['acceptable'] != true && mounted) {
        final issues = (quality['issues'] as List?)?.cast<String>() ?? [];
        final suggestion = quality['suggestion'] as String? ?? 'Try again';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('⚠️ ${issues.isNotEmpty ? issues.first : suggestion}'),
            action: SnackBarAction(label: 'Retake', onPressed: () => _pickAndValidate(isFront)),
            duration: const Duration(seconds: 5),
            backgroundColor: Colors.orange.shade800,
          ),
        );
      }
    } catch (_) {
      // Quality check failed silently — don't block the user
    }
  }

  Future<void> _analyze() async {
    if (_frontPath == null) return;

    // Warn if front quality is bad
    if (_frontQuality != null && _frontQuality!['acceptable'] != true) {
      final proceed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: const Color(0xFF1A1A2E),
          title: const Text('Image Quality Warning', style: TextStyle(color: Colors.white)),
          content: Text(
            'The front photo has quality issues:\n${(_frontQuality!['issues'] as List?)?.join('\n') ?? 'Unknown'}\n\nContinue anyway? Results may be less accurate.',
            style: TextStyle(color: Colors.white.withValues(alpha: 0.7)),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Retake')),
            TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Continue')),
          ],
        ),
      );
      if (proceed != true) return;
    }

    final heightCm = double.tryParse(_heightController.text) ?? 165.0;
    if (heightCm < 100 || heightCm > 250) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('⚠️ Height must be 100–250 cm')));
      }
      return;
    }

    final api = ref.read(apiClientProvider);
    setState(() {
      _analyzing = true;
      _statusText = 'Uploading photos...';
      _result = null;
    });

    try {
      setState(() => _statusText = _sidePath != null
          ? 'Analyzing front & side photos with AI Vision...'
          : 'Analyzing body proportions with AI Vision...');

      final resp = await api.analyzeBody(
        frontPath: _frontPath!,
        sidePath: _sidePath,
        heightCm: heightCm,
      );

      setState(() {
        _result = resp;
        _statusText = '';
        // Update stored measurements
        _storedMeasurements = {
          'has_profile': true,
          'measurements': resp['measurements'],
          'build_type': resp['build_type'],
          'confidence': resp['confidence'],
        };
      });

      if (mounted) {
        final conf = ((resp['confidence'] as num?) ?? 0.5) * 100;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Body analysis complete! ${conf.toInt()}% confidence. Saved to your profile.'),
            backgroundColor: const Color(0xFF2E7D32),
          ),
        );
      }
    } catch (e) {
      setState(() => _statusText = '');
      String msg = 'Analysis failed';

      // Extract error detail from DioException response body
      // DioException.toString() does NOT include the response body,
      // so we must check e.response?.data for the actual error type
      String errorDetail = '';
      int? confidencePercent;

      if (e is DioException && e.response?.data != null) {
        final data = e.response!.data;
        if (data is Map<String, dynamic>) {
          // FastAPI returns {"detail": {...}} for HTTPException
          final detail = data['detail'];
          if (detail is Map<String, dynamic>) {
            errorDetail = detail['error']?.toString() ?? '';
            confidencePercent = detail['confidence'] as int?;
          } else if (detail is String) {
            errorDetail = detail;
          }
        }
        errorDetail = errorDetail.isEmpty ? e.toString() : errorDetail;
      } else {
        errorDetail = e.toString();
      }

      if (errorDetail.contains('poor_image_quality') || errorDetail.contains('low_measurement_confidence')) {
        // Show detailed retake dialog with server suggestion if available
        if (mounted) {
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              backgroundColor: const Color(0xFF1A1A2E),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: Row(
                children: [
                  Icon(Icons.photo_camera, color: Colors.orange.shade300, size: 22),
                  const SizedBox(width: 10),
                  Expanded(child: Text(
                    confidencePercent != null
                        ? 'Confidence: $confidencePercent%'
                        : 'Better Photo Needed',
                    style: const TextStyle(color: Colors.white, fontSize: 17),
                  )),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'For precise tailoring measurements, please:',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13),
                  ),
                  const SizedBox(height: 14),
                  _retakeTip(Icons.accessibility_new, 'Stand upright, arms slightly out'),
                  _retakeTip(Icons.light_mode, 'Good, even lighting (no shadows)'),
                  _retakeTip(Icons.straighten, 'Wear form-fitting clothes'),
                  _retakeTip(Icons.crop_portrait, 'Full body: head to feet visible'),
                  _retakeTip(Icons.person_outline, 'Add a side photo for 95%+ accuracy'),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: Text('Retake Front', style: TextStyle(color: Colors.orange.shade300)),
                ),
              ],
            ),
          );
        }
        return;
      }

      msg = '❌ $errorDetail';
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red.shade800));
      }
    } finally {
      setState(() => _analyzing = false);
    }
  }

  Widget _retakeTip(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFFD4AF37), size: 18),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12))),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_storedMeasurements != null && !_isRetaking) {
      return _buildDashboard();
    }

    final measurements = _result?['measurements'] as Map<String, dynamic>?;
    final confidence = (_result?['confidence'] as num?)?.toDouble();
    final buildType = _result?['build_type'] as String?;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('Body Analysis'),
        centerTitle: true,
        leading: _storedMeasurements != null ? IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => setState(() => _isRetaking = false),
        ) : null,
        actions: [
          if (_storedMeasurements?['has_profile'] == true)
            IconButton(
              icon: const Icon(Icons.history, color: Color(0xFFD4AF37)),
              tooltip: 'Saved measurements',
              onPressed: () {
                setState(() {
                  _result = {
                    'measurements': _storedMeasurements!['measurements'],
                    'confidence': _storedMeasurements!['confidence'] ?? 0.9,
                    'build_type': _storedMeasurements!['build_type'] ?? 'average',
                  };
                });
              },
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildHeader(),
          const SizedBox(height: 20),

          // Photo cards
          Row(
            children: [
              Expanded(child: _PhotoCard(
                label: 'Front', sublabel: 'Required', icon: Icons.person,
                imagePath: _frontPath, quality: _frontQuality, required: true,
                onTap: () => _pickAndValidate(true),
              )),
              const SizedBox(width: 12),
              Expanded(child: _PhotoCard(
                label: 'Side', sublabel: 'Recommended', icon: Icons.person_outline,
                imagePath: _sidePath, quality: _sideQuality, required: false,
                onTap: () => _pickAndValidate(false),
              )),
            ],
          ),

          // Side photo benefit hint
          if (_frontPath != null && _sidePath == null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFD4AF37).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.2)),
              ),
              child: Row(
                children: [
                  Icon(Icons.tips_and_updates, color: Colors.amber.shade300, size: 16),
                  const SizedBox(width: 8),
                  Expanded(child: Text(
                    'Add a side photo for 92% accuracy (vs 85% front-only)',
                    style: TextStyle(color: Colors.amber.shade200, fontSize: 12),
                  )),
                ],
              ),
            ),
          ],

          const SizedBox(height: 16),
          _buildHeightInput(),
          const SizedBox(height: 16),

          // Analyze button
          _buildAnalyzeButton(),

          if (_statusText.isNotEmpty) ...[
            const SizedBox(height: 12),
            Center(child: Text(_statusText, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 13))),
          ],

          // Results
          if (measurements != null) ...[
            const SizedBox(height: 24),
            _buildResultsCard(measurements, confidence, buildType),
            const SizedBox(height: 12),
            // Saved indicator
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF2E7D32).withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF2E7D32).withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  Icon(Icons.save, color: Colors.green.shade300, size: 18),
                  const SizedBox(width: 10),
                  Expanded(child: Text(
                    'Measurements saved to your profile.\nThey will be used automatically when designing outfits.',
                    style: TextStyle(color: Colors.green.shade200, fontSize: 12, height: 1.4),
                  )),
                ],
              ),
            ),
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
            gradient: const LinearGradient(colors: [Color(0xFF8B1538), Color(0xFF4A148C)]),
            boxShadow: [BoxShadow(color: const Color(0xFF8B1538).withValues(alpha: 0.4), blurRadius: 20)],
          ),
          child: const Icon(Icons.straighten, color: Colors.white, size: 28),
        ),
        const SizedBox(height: 12),
        const Text('AI Body Measurement', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        Text(
          'Take full-body photos for precise measurements\nused in outfit design & tailoring',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white.withValues(alpha: 0.6), fontSize: 13, height: 1.4),
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
                const Text('Your Height', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
                Text('Calibration anchor for all measurements', style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 11)),
              ],
            ),
          ),
          SizedBox(
            width: 80,
            child: TextField(
              controller: _heightController,
              keyboardType: TextInputType.number,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                suffixText: 'cm',
                suffixStyle: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12),
                contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2))),
                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.2))),
                focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFFD4AF37))),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalyzeButton() {
    final canAnalyze = _frontPath != null && !_analyzing;
    return Container(
      width: double.infinity, height: 52,
      decoration: BoxDecoration(
        gradient: canAnalyze ? const LinearGradient(colors: [Color(0xFF8B1538), Color(0xFF6A0F2B)]) : null,
        color: !canAnalyze ? Colors.grey.shade800 : null,
        borderRadius: BorderRadius.circular(16),
        boxShadow: canAnalyze ? [BoxShadow(color: const Color(0xFF8B1538).withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 4))] : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: canAnalyze ? _analyze : null,
          borderRadius: BorderRadius.circular(16),
          child: Center(
            child: _analyzing
                ? const Row(mainAxisSize: MainAxisSize.min, children: [
                    SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                    SizedBox(width: 10),
                    Text('Analyzing with AI Vision...', style: TextStyle(color: Colors.white, fontSize: 15)),
                  ])
                : Row(mainAxisSize: MainAxisSize.min, children: [
                    const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      _sidePath != null ? 'Analyze (Front + Side)' : 'Analyze Body',
                      style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ]),
          ),
        ),
      ),
    );
  }

  Widget _buildResultsCard(Map<String, dynamic> measurements, double? confidence, String? buildType) {
    final confidencePct = ((confidence ?? 0.5) * 100).toInt();
    // 3-tier confidence display
    final Color confColor;
    final IconData confIcon;
    final String confLabel;
    if (confidencePct >= 75) {
      confColor = Colors.green.shade300;
      confIcon = Icons.verified;
      confLabel = '$confidencePct% Confidence • AI Verified';
    } else if (confidencePct >= 55) {
      confColor = Colors.amber.shade300;
      confIcon = Icons.check_circle_outline;
      confLabel = '$confidencePct% Confidence • Good Estimate';
    } else {
      confColor = Colors.orange.shade300;
      confIcon = Icons.info_outline;
      confLabel = '$confidencePct% Confidence • Approximate';
    }
    final isHighConf = confidencePct >= 55; // Used for border styling
    final bt = buildType ?? measurements['_vlm_build_type'] as String? ?? 'average';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [Colors.white.withValues(alpha: 0.08), Colors.white.withValues(alpha: 0.03)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: isHighConf ? const Color(0xFFD4AF37).withValues(alpha: 0.3) : Colors.white.withValues(alpha: 0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: confColor.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(confIcon, color: confColor, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Your Measurements', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                    Text(confLabel, style: TextStyle(color: confColor, fontSize: 12)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFD4AF37).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        'Build: ${bt.toUpperCase()}',
                        style: const TextStyle(color: Color(0xFFD4AF37), fontSize: 11, fontWeight: FontWeight.w600),
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
              value: confidence ?? 0.5,
              backgroundColor: Colors.white.withValues(alpha: 0.1),
              valueColor: AlwaysStoppedAnimation(confColor),
              minHeight: 4,
            ),
          ),
          const SizedBox(height: 20),
          _MeasurementGrid(measurements: measurements),
        ],
      ),
    );
  }

  Widget _buildDashboard() {
    final measurements = _storedMeasurements!['measurements'] as Map<String, dynamic>?;
    final b64Photo = measurements?['_front_photo_b64'] as String?;
    final gender = measurements?['_vlm_gender'] as String? ?? 'Not specified';
    final buildType = _storedMeasurements!['build_type'] as String? ?? 'Average';

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('My Profile', style: TextStyle(fontWeight: FontWeight.w600)),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: Container(
              width: 140,
              height: 140,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFFD4AF37), width: 3),
                boxShadow: [
                  BoxShadow(color: const Color(0xFFD4AF37).withValues(alpha: 0.2), blurRadius: 20, spreadRadius: 2),
                ],
              ),
              child: ClipOval(
                child: b64Photo != null
                    ? Image.memory(base64Decode(b64Photo), fit: BoxFit.cover)
                    : Container(color: Colors.white10, child: const Icon(Icons.person, size: 60, color: Colors.white54)),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A2E),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFD4AF37).withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.verified, color: Color(0xFFD4AF37), size: 24),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Wired to AI Agent\nThis data is actively used to personalize your style recommendations and tailor designs.',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 12, height: 1.4),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text('BODY PROFILE', style: TextStyle(color: const Color(0xFFD4AF37), fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
          const SizedBox(height: 12),
          _buildInfoRow('Gender', gender.toUpperCase()),
          const Divider(color: Colors.white10),
          _buildInfoRow('Build Type', buildType.toUpperCase()),
          const Divider(color: Colors.white10),
          if (measurements != null) ...[
            const SizedBox(height: 24),
            const Text('KEY MEASUREMENTS', style: TextStyle(color: const Color(0xFFD4AF37), fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              childAspectRatio: 2.5,
              children: [
                _buildMeasurementBox('Chest', measurements['chest_cm']),
                _buildMeasurementBox('Waist', measurements['waist_cm']),
                _buildMeasurementBox('Hips', measurements['hip_cm']),
                _buildMeasurementBox('Inseam', measurements['inseam_cm']),
              ],
            ),
          ],
          const SizedBox(height: 40),
          OutlinedButton.icon(
            icon: const Icon(Icons.camera_alt, color: Colors.white),
            label: const Text('Update Avatar & Measurements', style: TextStyle(color: Colors.white)),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              side: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => setState(() => _isRetaking = true),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.6), fontSize: 15)),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildMeasurementBox(String label, dynamic value) {
    return Container(
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.05), borderRadius: BorderRadius.circular(12)),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text('${value != null ? (value as num).toInt() : "--"}', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(width: 4),
              const Text('cm', style: TextStyle(color: Color(0xFFD4AF37), fontSize: 12)),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Measurement Grid ─────────────────────────────────────────────────────

class _MeasurementGrid extends StatelessWidget {
  const _MeasurementGrid({required this.measurements});
  final Map<String, dynamic> measurements;

  @override
  Widget build(BuildContext context) {
    final items = <MapEntry<String, String>>[];
    void add(String key, String label, String unit) {
      final val = measurements[key];
      if (val != null) items.add(MapEntry(label, '$val $unit'));
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
        crossAxisCount: 3, childAspectRatio: 1.3, crossAxisSpacing: 10, mainAxisSpacing: 10,
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
              Text(item.value, style: const TextStyle(color: Color(0xFFD4AF37), fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(item.key, style: TextStyle(color: Colors.white.withValues(alpha: 0.6), fontSize: 11), textAlign: TextAlign.center),
            ],
          ),
        );
      },
    );
  }
}

// ── Photo Card with Quality Indicator ────────────────────────────────────

class _PhotoCard extends StatelessWidget {
  const _PhotoCard({
    required this.label, required this.sublabel, required this.icon,
    required this.imagePath, required this.quality, required this.required,
    required this.onTap,
  });
  final String label, sublabel;
  final IconData icon;
  final String? imagePath;
  final Map<String, dynamic>? quality;
  final bool required;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isGoodQuality = quality?['acceptable'] == true;
    final hasQuality = quality != null;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: imagePath != null
                ? (hasQuality
                    ? (isGoodQuality ? Colors.green.withValues(alpha: 0.5) : Colors.orange.withValues(alpha: 0.5))
                    : const Color(0xFFD4AF37).withValues(alpha: 0.5))
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
                    Image.file(File(imagePath!), fit: BoxFit.cover),
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter, end: Alignment.bottomCenter,
                          colors: [Colors.transparent, Colors.black.withValues(alpha: 0.7)],
                        ),
                      ),
                    ),
                    // Quality badge
                    if (hasQuality)
                      Positioned(
                        top: 8, left: 8,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: isGoodQuality ? Colors.green.withValues(alpha: 0.8) : Colors.orange.withValues(alpha: 0.8),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(mainAxisSize: MainAxisSize.min, children: [
                            Icon(isGoodQuality ? Icons.check : Icons.warning_amber, color: Colors.white, size: 12),
                            const SizedBox(width: 4),
                            Text(isGoodQuality ? 'Good' : 'Retake', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
                          ]),
                        ),
                      ),
                    Positioned(
                      bottom: 10, left: 10, right: 10,
                      child: Row(children: [
                        Icon(Icons.check_circle, color: isGoodQuality ? Colors.green : const Color(0xFFD4AF37), size: 16),
                        const SizedBox(width: 6),
                        Text(label, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                      ]),
                    ),
                    Positioned(
                      top: 8, right: 8,
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.5), borderRadius: BorderRadius.circular(8)),
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
                    Text(label, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        color: required ? const Color(0xFF8B1538).withValues(alpha: 0.3) : Colors.white.withValues(alpha: 0.05),
                      ),
                      child: Text(sublabel, style: TextStyle(
                        color: required ? Colors.red.shade200 : Colors.white.withValues(alpha: 0.4),
                        fontSize: 10, fontWeight: FontWeight.w500,
                      )),
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
