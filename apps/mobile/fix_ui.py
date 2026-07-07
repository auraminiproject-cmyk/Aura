import re

def fix_design_screen():
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\design\design_screen.dart', 'r', encoding='utf-8') as f:
        content = f.read()

    # Change all Colors.white text to Color(0xFF1A237E)
    content = content.replace('Colors.white', 'Color(0xFF1A237E)')
    # Fix broken syntax caused by literal replacements
    content = content.replace('Colors.green.shade300', 'Color(0xFF4A90E2)')
    
    content = re.sub(r'const Color\(0xFF8B1538\)\.withValues\(alpha: 0\.3\)', r'Colors.white', content)
    content = re.sub(r'const Color\(0xFF4A148C\)\.withValues\(alpha: 0\.3\)', r'Colors.white', content)
    
    content = content.replace('const LinearGradient(colors: [Color(0xFF8B1538), Color(0xFF6A0F2B)])', 'color: Colors.white')
    content = content.replace('gradient: color: Colors.white', 'color: Colors.white')
    
    content = re.sub(r'const Color\(0xFF8B1538\)\.withValues\(alpha: 0\.15\)', r'Colors.white', content)
    content = re.sub(r'const Color\(0xFF4A148C\)\.withValues\(alpha: 0\.1\)', r'Colors.white', content)
    
    content = content.replace('const LinearGradient(colors: [Color(0xFF8B1538), Color(0xFF4A148C)])', 'color: Colors.white')
    content = content.replace('gradient: color: Colors.white', 'color: Colors.white')
    
    content = re.sub(r'const Color\(0xFF1B5E20\)\.withValues\(alpha: 0\.3\)', r'Colors.white', content)
    
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\design\design_screen.dart', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_chat_screen():
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\chat\chat_screen.dart', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Tailoring Card Background
    content = content.replace('gradient: LinearGradient(colors: [\n            Color(0xFF1B5E20).withValues(alpha: 0.4),\n            Color(0xFF2E7D32).withValues(alpha: 0.3),\n          ]),', 'color: Colors.white,')
    content = content.replace('color: Colors.white.withValues(alpha: 0.85)', 'color: Color(0xFF1A237E)')

    # Recording Banner
    content = content.replace('gradient: LinearGradient(\n              colors: [\n                Color.lerp(\n                  Color(0xFF8B1538).withValues(alpha: 0.8),\n                  Color(0xFFFF1744).withValues(alpha: 0.9),\n                  _pulseCtrl.value,\n                )!,\n                Color(0xFF4A148C).withValues(alpha: 0.9),\n              ],\n            ),', 'color: Colors.white,')
    content = content.replace('color: Colors.white.withValues(alpha: 0.15)', 'color: Colors.white')
    content = content.replace('color: Colors.white.withValues(alpha: 0.2)', 'color: Color(0xFF1A237E).withValues(alpha: 0.2)')
    content = content.replace('child: const Icon(Icons.stop_rounded, color: Colors.white, size: 20),', 'child: const Icon(Icons.stop_rounded, color: Color(0xFF1A237E), size: 20),')

    # Playing Banner
    content = content.replace('gradient: LinearGradient(\n          colors: [\n            Color(0xFF1B5E20).withValues(alpha: 0.8),\n            Color(0xFF004D40).withValues(alpha: 0.8),\n          ],\n        ),', 'color: Colors.white,')
    
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\chat\chat_screen.dart', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_profile_screen():
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\avatar\profile_screen.dart', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('colors: [Colors.transparent, Colors.black.withValues(alpha: 0.7)]', 'colors: [Colors.transparent, Colors.white.withValues(alpha: 0.9)]')
    content = content.replace('color: Colors.black.withValues(alpha: 0.5)', 'color: Colors.white.withValues(alpha: 0.9)')
    
    with open(r'd:\Aura-gem\fashion-ai\apps\mobile\lib\features\avatar\profile_screen.dart', 'w', encoding='utf-8') as f:
        f.write(content)

fix_design_screen()
fix_chat_screen()
fix_profile_screen()
