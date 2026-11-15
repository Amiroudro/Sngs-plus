/// Sarangsho Plus — Flutter mobile app.
/// Bengali-first, fully offline, free, no login, no ads, no tracking.
/// Data: bundled edition JSONs (assets/editions/). No network at runtime.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'data/loader.dart';
import 'screens/current_affairs_screen.dart';
import 'screens/editorial_screen.dart';
import 'screens/home_screen.dart';
import 'screens/library_screen.dart';
import 'screens/profile_screen.dart';
import 'services/app_update_service.dart';
import 'state/app_state.dart';
import 'widgets/app_theme.dart';

void main() {
  // Status bar: transparent so the app draws edge to edge, with dark
  // icons on the light paper (light icons once dark mode is on — the
  // AnnotatedRegion below keeps it in sync with the theme).
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      statusBarBrightness: Brightness.light,
      systemNavigationBarColor: Colors.white,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const SarangshoPlusApp());
}

/// Status-bar + navigation-bar style for the current theme. Light:
/// dark icons on the white paper. Dark: light icons on the dark paper.
SystemUiOverlayStyle _overlayStyleFor(bool dark) => SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: dark ? Brightness.light : Brightness.dark,
      statusBarBrightness: dark ? Brightness.dark : Brightness.light,
      systemNavigationBarColor:
          dark ? AppColors.darkSurface : AppColors.surface,
      systemNavigationBarIconBrightness:
          dark ? Brightness.light : Brightness.dark,
    );

class SarangshoPlusApp extends StatefulWidget {
  const SarangshoPlusApp({super.key});

  @override
  State<SarangshoPlusApp> createState() => _SarangshoPlusAppState();
}

class _SarangshoPlusAppState extends State<SarangshoPlusApp> {
  final AppState _state = AppState();
  bool _ready = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  Future<void> _boot() async {
    try {
      await _state.init();
      final result = await loadEditions();
      await _state.setEditions(
        result.editions,
        result.correctConsecutive,
        result.correctRule,
      );
      setState(() => _ready = true);
      // Phase 5: check for new editions once at start, against the
      // default Pages URL (or a stored override). Any failure
      // leaves the bundled editions in place, silently.
      await refreshEditions(_state);
      // Self-update (2013): check GitHub for a newer app version.
      // Never blocks launch and never fails loudly — no update, no
      // network, or a bad version file just means no banner.
      try {
        final update = await const AppUpdateService().checkForUpdate();
        if (update != null) _state.setAvailableUpdate(update);
      } catch (_) {
        // No banner. The app works exactly as before.
      }
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _state,
      builder: (context, _) {
        final strings = _state.strings;
        return AnnotatedRegion<SystemUiOverlayStyle>(
          value: _overlayStyleFor(_state.darkMode),
          child: MaterialApp(
            title: strings['appName'] ?? 'সারাংশ প্লাস',
            debugShowCheckedModeBanner: false,
            theme: buildLightTheme(),
            darkTheme: buildDarkTheme(),
            themeMode: _state.darkMode ? ThemeMode.dark : ThemeMode.light,
            builder: (context, child) {
              final base = MediaQuery.textScalerOf(context);
              final factor =
                  (base.scale(1.0) * _state.fontScale).clamp(0.5, 3.0);
              return MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(factor),
                ),
                child: child!,
              );
            },
            home: _ready
                ? AppShell(state: _state)
                : _LoadingScreen(
                    error: _error,
                    strings: strings,
                    onRetry: () {
                      setState(() => _error = null);
                      _boot();
                    },
                  ),
          ),
        );
      },
    );
  }
}

/// Skeleton loading screen shaped like the Home that is coming:
/// masthead (red square + wordmark bar + dateline bar + 2px ink rule),
/// then numbered-row skeletons with hairlines.
class _LoadingScreen extends StatelessWidget {
  final String? error;
  final Map<String, String> strings;
  final VoidCallback onRetry;

  const _LoadingScreen({
    required this.error,
    required this.strings,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return Scaffold(
        body: EmptyState(
          icon: Icons.newspaper,
          body: strings['errorLoading'] ?? 'Could not load.',
          actionLabel: strings['retry'] ?? 'Try again',
          onAction: onRetry,
        ),
      );
    }
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.screen),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.s16),
              Row(
                children: [
                  Container(width: 40, height: 40, color: accent),
                  const SizedBox(width: 12),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SkeletonBox(height: 30, width: 180),
                      SizedBox(height: 6),
                      SkeletonBox(height: 12, width: 140),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const SkeletonBox(height: 13, width: 220),
              const SizedBox(height: 12),
              Container(
                height: 2,
                color: dark ? AppColors.darkInk : AppColors.ink,
              ),
              const SizedBox(height: 16),
              for (var i = 0; i < 3; i++) ...[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(width: 32, height: 40, color: accent),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SkeletonBox(height: 16, width: 200),
                          SizedBox(height: 8),
                          SkeletonBox(height: 12, width: 260),
                          SizedBox(height: 6),
                          SkeletonBox(height: 12, width: 180),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  height: 1,
                  color: dark ? AppColors.darkHairline : AppColors.hairline,
                ),
                const SizedBox(height: 16),
              ],
              Center(
                child: Text(
                  strings['loading'] ?? 'Loading…',
                  style: TextStyle(
                    fontSize: 13,
                    color: dark
                        ? AppColors.darkInkSecondary
                        : AppColors.inkSecondary,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// The 5-tab shell: Home / Current Affairs / Editorial / Library /
/// Profile. English and Quiz are reached from Home, keeping the bottom
/// bar at 5 tabs. IndexedStack keeps each tab's scroll position.
class AppShell extends StatefulWidget {
  final AppState state;

  const AppShell({super.key, required this.state});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final pages = [
      HomeScreen(state: state),
      CurrentAffairsScreen(state: state),
      EditorialScreen(state: state),
      LibraryScreen(state: state),
      ProfileScreen(state: state),
    ];
    Widget navIcon(IconData outline, IconData filled, bool active) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 24,
            height: 3,
            color: active ? accent : Colors.transparent,
          ),
          const SizedBox(height: 2),
          Icon(active ? filled : outline, size: 24),
        ],
      );
    }

    return Scaffold(
      // Top SafeArea ON: without it the masthead and every tab header
      // start at y=0 and slide under the status bar (time, battery,
      // icons). Bottom stays off — the bottom navigation bar sits
      // above the system bar on its own.
      body: SafeArea(
        top: true,
        bottom: false,
        child: IndexedStack(index: _index, children: pages),
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: dark ? AppColors.darkSurface : AppColors.surface,
          border: Border(
            top: BorderSide(
              color: dark ? AppColors.darkHairline : AppColors.hairline,
            ),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _index,
          type: BottomNavigationBarType.fixed,
          onTap: (i) => setState(() => _index = i),
          items: [
            BottomNavigationBarItem(
              icon: navIcon(Icons.home_outlined, Icons.home, _index == 0),
              label: state.t('home'),
            ),
            BottomNavigationBarItem(
              icon: navIcon(
                Icons.newspaper_outlined,
                Icons.newspaper,
                _index == 1,
              ),
              // Short label: the full 'সাম্প্রতিক ঘটনা' truncates to
              // 'সাম্প্রতিক ঘ…' in the 5-item fixed bar.
              label: state.t('navCurrentAffairs'),
            ),
            BottomNavigationBarItem(
              icon: navIcon(
                Icons.edit_note_outlined,
                Icons.edit_note,
                _index == 2,
              ),
              label: state.t('editorial'),
            ),
            BottomNavigationBarItem(
              icon: navIcon(
                Icons.bookmark_outline,
                Icons.bookmark,
                _index == 3,
              ),
              label: state.t('library'),
            ),
            BottomNavigationBarItem(
              icon: navIcon(
                Icons.person_outline,
                Icons.person,
                _index == 4,
              ),
              label: state.t('profile'),
            ),
          ],
        ),
      ),
    );
  }
}
