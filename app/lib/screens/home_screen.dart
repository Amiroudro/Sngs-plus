/// Home tab — the flagship. NEXUS editorial layout:
/// masthead (logo block + wordmark + dateline + edition switcher),
/// hairline search field, top-story hero FIRST, then English / Quiz
/// as text rows, section index, numbered story rows separated by
/// hairlines. Pull down to check for new editions (and re-read the
/// bundled editions).
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/loader.dart';
import '../data/sections.dart';
import '../data/strings.dart';
import '../models.dart';
import '../services/app_update_service.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/bangla_review_notice.dart';
import '../widgets/masthead.dart';
import '../widgets/story_card.dart';
import 'english_screen.dart';
import 'quiz_screen.dart';
import 'search_screen.dart';
import 'story_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  final AppState state;

  const HomeScreen({super.key, required this.state});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _section = 'All';

  Future<void> _refresh() async {
    // Phase 5: pull-to-refresh also checks the remote index (default
    // Pages URL, or a stored override) and re-reads the editions;
    // any failure leaves the bundled editions in place.
    await refreshEditions(widget.state);
  }

  void _openStory(BuildContext context, Edition edition, Story story) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => StoryDetailScreen(
          edition: edition,
          story: story,
          state: widget.state,
        ),
      ),
    );
  }

  void _showEditionSheet(BuildContext context) {
    final state = widget.state;
    final lang = state.lang;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(AppRadii.sheet),
        ),
      ),
      builder: (_) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 8),
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.inkFaint.withValues(alpha: 0.5),
              borderRadius: AppShapes.metaPill,
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                state.t('editionsTitle'),
                style: AppType.section,
              ),
            ),
          ),
          Flexible(
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: state.editions.length,
              itemBuilder: (context, i) {
                final e = state.editions[i];
                final selected = e.date == state.selectedEdition?.date;
                return InkWell(
                  onTap: () {
                    state.selectEdition(e.date);
                    Navigator.of(context).pop();
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                storyDigits(
                                  '${formatEditionDate(e.date, lang)} — '
                                  '${e.storyCount} ${state.t('stories')} • '
                                  '${e.wordCount} ${state.t('words')} • '
                                  '${e.mcqCount} ${state.t('mcqs')}',
                                  lang,
                                ),
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: selected
                                      ? FontWeight.w800
                                      : FontWeight.w400,
                                  color: selected ? accent : null,
                                ),
                              ),
                            ),
                            if (selected)
                              Icon(Icons.check, size: 20, color: accent),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Container(
                          height: 1,
                          color: dark
                              ? AppColors.darkHairline
                              : AppColors.hairline,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final edition = state.selectedEdition;
    if (edition == null) {
      return EmptyState(
        icon: Icons.newspaper,
        body: state.t('errorLoading'),
        actionLabel: state.t('retry'),
        onAction: _refresh,
      );
    }
    final lang = state.lang;
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? state.t('greetingMorning')
        : hour < 18
            ? state.t('greetingDay')
            : state.t('greetingEvening');
    final dark = Theme.of(context).brightness == Brightness.dark;

    final allStories = _section == 'All'
        ? edition.stories
        : edition.stories
            .where((s) => sectionFor(s.category) == _section)
            .toList();
    final listStories = (_section == 'All' && allStories.isNotEmpty)
        ? allStories.sublist(1)
        : allStories;
    final topStory =
        (_section == 'All' && allStories.isNotEmpty) ? allStories.first : null;
    final heroShown = topStory != null;

    return RefreshIndicator(
      onRefresh: _refresh,
      color: AppColors.pink,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverToBoxAdapter(
            child: Masthead(
              state: state,
              greeting: greeting,
              onEditionTap: () => _showEditionSheet(context),
            ),
          ),
          if (lang == 'bn' && edition.banglaPendingReview)
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.fromLTRB(16, 12, 16, 0),
                child: BanglaReviewNotice(),
              ),
            ),
          // Self-update (2013): when GitHub advertises a newer app
          // version, a banner offers the one-tap update. Dismissing
          // hides it for this session; it returns on the next
          // launch while a newer version is still available.
          if (state.availableUpdate != null)
            SliverToBoxAdapter(
              child: _UpdateBanner(
                state: state,
                info: state.availableUpdate!,
              ),
            ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: InkWell(
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => SearchScreen(state: state),
                  ),
                ),
                borderRadius: BorderRadius.circular(AppRadii.small),
                child: Container(
                  height: 48,
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: dark ? AppColors.darkHairline : AppColors.hairline,
                    ),
                    borderRadius: BorderRadius.circular(AppRadii.small),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.search,
                        color: AppColors.secondaryFor(
                          Theme.of(context).brightness,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          state.t('searchHint'),
                          style: TextStyle(
                            color: AppColors.secondaryFor(
                              Theme.of(context).brightness,
                            ),
                            fontSize: 14,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          // Order (Phase 2): masthead → search → TOP STORY hero →
          // English / Quiz rows → section index → numbered rows.
          // The first news story is the first content after the
          // masthead/search, not the English and Quiz rows.
          if (topStory != null)
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.only(top: 12),
                child: StoryCard(
                  edition: edition,
                  story: topStory,
                  state: state,
                  hero: true,
                  onTap: () => _openStory(context, edition, topStory),
                ),
              ),
            )
          else
            SliverToBoxAdapter(
              child: Container(
                height: 2,
                margin: const EdgeInsets.only(top: 12),
                color: dark ? AppColors.darkInk : AppColors.ink,
              ),
            ),
          SliverToBoxAdapter(
            child: Column(
              children: [
                _HomeTextRow(
                  icon: Icons.translate,
                  title: state.t('english'),
                  sub: storyDigits(
                      '${edition.wordCount} ${state.t('words')} • ${edition.phraseCount} ${state.t('phrases')}',
                      lang),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => EnglishScreen(state: state),
                    ),
                  ),
                ),
                _HomeTextRow(
                  icon: Icons.quiz_outlined,
                  title: state.t('quiz'),
                  sub: storyDigits(
                      '${edition.mcqCount} ${state.t('mcqs')} • ${state.t('practiceQuiz')}',
                      lang),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => QuizScreen(state: state),
                    ),
                  ),
                ),
              ],
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  NewsSectionLabel.heading(
                    '${state.t('todaysEdition')} — ${formatEditionDate(edition.date, lang)}',
                  ),
                  // NOTE: the edition's `coverage` field ("1 November
                  // 2026 (Asia/Dhaka) — backfilled edition") is internal
                  // metadata and is deliberately NOT shown here.
                  const SizedBox(height: 12),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _SectionItem(
                          label: state.t('all'),
                          selected: _section == 'All',
                          onTap: () => setState(() => _section = 'All'),
                        ),
                        for (final s in sixSections)
                          _SectionItem(
                            label: sectionName(s, lang),
                            selected: _section == s,
                            onTap: () => setState(() => _section = s),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, i) {
                final story = listStories[i];
                return StoryCard(
                  edition: edition,
                  story: story,
                  state: state,
                  // Hero is 01, so list rows start at 02 when shown.
                  index: heroShown ? i + 1 : i,
                  showDivider: i < listStories.length - 1,
                  onTap: () => _openStory(context, edition, story),
                );
              },
              childCount: listStories.length,
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 24)),
        ],
      ),
    );
  }
}

/// Self-update banner (2013): shown when GitHub advertises a newer
/// app version. Update opens the APK URL in the browser — the browser
/// downloads it and Android's installer takes over, one Install tap.
/// Later hides the banner for this session.
class _UpdateBanner extends StatelessWidget {
  final AppState state;
  final UpdateInfo info;

  const _UpdateBanner({required this.state, required this.info});

  Future<void> _openUpdate() async {
    final uri = Uri.tryParse(info.apkUrl);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
        decoration: BoxDecoration(
          color: accent.withValues(alpha: 0.10),
          border: Border.all(color: accent.withValues(alpha: 0.45)),
          borderRadius: BorderRadius.circular(AppRadii.small),
        ),
        child: Row(
          children: [
            Icon(Icons.system_update, size: 22, color: accent),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    state.t('updateAvailable'),
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${state.t('updateVersion')} ${info.versionName}',
                    style: TextStyle(
                      fontSize: 13,
                      color: dark
                          ? AppColors.darkInkSecondary
                          : AppColors.inkSecondary,
                    ),
                  ),
                ],
              ),
            ),
            TextButton(
              onPressed: _openUpdate,
              child: Text(state.t('updateNow')),
            ),
            IconButton(
              onPressed: state.dismissUpdate,
              icon: const Icon(Icons.close, size: 20),
              tooltip: state.t('updateLater'),
            ),
          ],
        ),
      ),
    );
  }
}

/// English / Quiz as a text row: red square icon tile + title +
/// counts + red square arrow. Hairline below.
class _HomeTextRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String sub;
  final VoidCallback onTap;

  const _HomeTextRow({
    required this.icon,
    required this.title,
    required this.sub,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final primary = AppColors.primaryFor(Theme.of(context).brightness);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    color: primary,
                    child: Icon(icon, color: Colors.white, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Text(
                          sub,
                          style: TextStyle(
                            fontSize: 12,
                            color: dark
                                ? AppColors.darkInkSecondary
                                : AppColors.inkSecondary,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  Container(
                    width: 32,
                    height: 32,
                    color: primary,
                    child: const Icon(
                      Icons.arrow_forward,
                      size: 18,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
            Container(
              height: 1,
              margin: const EdgeInsets.symmetric(horizontal: 16),
              color: dark ? AppColors.darkHairline : AppColors.hairline,
            ),
          ],
        ),
      ),
    );
  }
}

/// Section index item: plain text, active = red + 2px red underline.
class _SectionItem extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _SectionItem({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final dark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.only(right: 18),
        child: Column(
          children: [
            Padding(
              // 14px vertical: the index item is a tap target and
              // must clear the 44px floor (~46px total with the 14px
              // label + 2px underline); 8px gave only ~35px.
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: selected ? FontWeight.w800 : FontWeight.w400,
                  color: selected
                      ? accent
                      : (dark
                          ? AppColors.darkInkSecondary
                          : AppColors.inkSecondary),
                ),
              ),
            ),
            Container(
              width: 24,
              height: 2,
              color: selected ? accent : Colors.transparent,
            ),
          ],
        ),
      ),
    );
  }
}
