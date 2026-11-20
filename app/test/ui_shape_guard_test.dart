/// Guard test: screens and widgets must not hard-code corner radii
/// or raw colours. Shapes come from AppShapes / AppBox and colours from
/// AppColors, all defined in lib/widgets/app_theme.dart. This is what
/// lets one edit in that file restyle every page, and it stops a new
/// edit (human or AI) from quietly bypassing the design layer.
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarangsho_plus/widgets/app_theme.dart';

void main() {
  test('no hard-coded radii or raw colours outside app_theme.dart', () {
    final forbidden = <RegExp>[
      RegExp(r'BorderRadius\.(circular|all|only|vertical|horizontal)\('),
      RegExp(r'(?<![A-Za-z])Radius\.circular\('),
      RegExp(r'Color\(0x[0-9A-Fa-f]+\)'),
    ];
    final offenders = <String>[];
    final lib = Directory('lib');
    expect(lib.existsSync(), isTrue, reason: 'run from the app/ directory');

    for (final entity in lib.listSync(recursive: true)) {
      if (entity is! File || !entity.path.endsWith('.dart')) continue;
      final normalised = entity.path.replaceAll('\\', '/');
      if (normalised.endsWith('lib/widgets/app_theme.dart')) continue;
      final lines = entity.readAsLinesSync();
      for (var i = 0; i < lines.length; i++) {
        final line = lines[i];
        if (line.trimLeft().startsWith('//')) continue;
        for (final pattern in forbidden) {
          if (pattern.hasMatch(line)) {
            offenders.add('$normalised:${i + 1}: ${line.trim()}');
          }
        }
      }
    }

    expect(
      offenders,
      isEmpty,
      reason: 'Use AppShapes / AppBox / AppColors from '
          'lib/widgets/app_theme.dart instead:\n${offenders.join('\n')}',
    );
  });

  test('every AppShape resolves to the matching AppShapes radius', () {
    expect(AppShape.box.radius, AppShapes.box);
    expect(AppShape.small.radius, AppShapes.small);
    expect(AppShape.medium.radius, AppShapes.medium);
    expect(AppShape.soft.radius, AppShapes.soft);
    expect(AppShape.round.radius, AppShapes.round);
    expect(AppShape.circle.radius, AppShapes.round);
    expect(AppShape.sheet.radius, AppShapes.sheet);
  });

  testWidgets('AppBox renders each shape without throwing', (tester) async {
    for (final shape in [null, ...AppShape.values]) {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: SizedBox(
                width: 80,
                height: 80,
                child: AppBox(
                  shape: shape,
                  role: AppShapes.cardSoft,
                  color: AppColors.forest,
                  child: const SizedBox.shrink(),
                ),
              ),
            ),
          ),
        ),
      );
      expect(tester.takeException(), isNull, reason: 'shape: $shape');
    }
  });
}
