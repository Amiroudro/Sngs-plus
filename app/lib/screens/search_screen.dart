/// Search across all editions: story headlines + summaries (in the
/// current display language) and word headwords + Bangla meanings.
/// Recent searches persist (max 8); matches are highlighted in red.
/// Story hits are numbered rows; word hits are collapsed rows that
/// expand inline.
library;

import 'package:flutter/material.dart';

import '../data/strings.dart';
import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/story_card.dart';
import '../widgets/word_card.dart';
import 'story_detail_screen.dart';
import 'word_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  final AppState state;

  const SearchScreen({super.key, required this.state});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _runSearch(String q) {
    final query = q.trim();
    setState(() => _query = query);
    if (query.isNotEmpty) widget.state.addRecentSearch(query);
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final lang = state.lang;
    final dark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColors.accentFor(Theme.of(context).brightness);
    final q = _query.trim().toLowerCase();

    final storyHits = <({Edition edition, Story story})>[];
    final wordHits = <({Edition edition, VocabWord word})>[];
    if (q.isNotEmpty) {
      for (final edition in state.editions) {
        for (final story in edition.stories) {
          final haystack =
              '${story.headlineIn(lang)} ${story.summaryIn(lang)} ${story.headline} ${story.summary}'
                  .toLowerCase();
          if (haystack.contains(q)) {
            storyHits.add((edition: edition, story: story));
          }
        }
        for (final word in [...edition.words, ...edition.revisionWords]) {
          final haystack =
              '${word.headword} ${word.banglaMeaning ?? ''} ${word.englishDefinition ?? ''}'
                  .toLowerCase();
          if (haystack.contains(q)) {
            wordHits.add((edition: edition, word: word));
          }
        }
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(state.t('search')),
        bottom: appBarHairline(context),
      ),
      body: SafeArea(
        top: false,
        bottom: true,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _controller,
                autofocus: true,
                textInputAction: TextInputAction.search,
                decoration: InputDecoration(
                  hintText: state.t('searchHint'),
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _query.isEmpty
                      ? null
                      : IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _controller.clear();
                            setState(() => _query = '');
                          },
                        ),
                ),
                onChanged: (v) => setState(() => _query = v),
                onSubmitted: _runSearch,
              ),
            ),
            if (q.isEmpty)
              Expanded(
                child: state.recentSearches.isEmpty
                    ? EmptyState(
                        icon: Icons.search,
                        body: state.t('typeToSearch'),
                      )
                    : ListView(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  state.t('recentSearches'),
                                  style: const TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                              TextButton(
                                onPressed: () => state.clearRecentSearches(),
                                child: Text(state.t('clear')),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: state.recentSearches
                                .map(
                                  (r) => ActionChip(
                                    label: Text(r),
                                    avatar: const Icon(
                                      Icons.history,
                                      size: 16,
                                    ),
                                    backgroundColor: dark
                                        ? AppColors.darkSurface
                                        : AppColors.surface,
                                    side: BorderSide(
                                      color: dark
                                          ? AppColors.darkHairline
                                          : AppColors.hairline,
                                    ),
                                    onPressed: () {
                                      _controller.text = r;
                                      _runSearch(r);
                                    },
                                  ),
                                )
                                .toList(),
                          ),
                        ],
                      ),
              )
            else if (storyHits.isEmpty && wordHits.isEmpty)
              Expanded(
                child: EmptyState(
                  icon: Icons.search_off,
                  body: state.t('noResults'),
                ),
              )
            else
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.only(bottom: 16),
                  children: [
                    if (storyHits.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
                        child: Text.rich(
                          TextSpan(
                            children: [
                              TextSpan(
                                text: storyDigits(
                                    '${storyHits.length} ', lang),
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w800,
                                  color: accent,
                                ),
                              ),
                              TextSpan(
                                text: state.t('storiesFound'),
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    for (var i = 0; i < storyHits.length; i++)
                      StoryCard(
                        edition: storyHits[i].edition,
                        story: storyHits[i].story,
                        state: state,
                        index: i,
                        highlight: _query.trim(),
                        showDivider: i < storyHits.length - 1,
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => StoryDetailScreen(
                              edition: storyHits[i].edition,
                              story: storyHits[i].story,
                              state: state,
                            ),
                          ),
                        ),
                      ),
                    if (wordHits.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                        child: Text.rich(
                          TextSpan(
                            children: [
                              TextSpan(
                                text: storyDigits(
                                    '${wordHits.length} ', lang),
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w800,
                                  color: accent,
                                ),
                              ),
                              TextSpan(
                                text: state.t('wordsFound'),
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    for (final hit in wordHits)
                      ExpandableWordRow(
                        edition: hit.edition,
                        word: hit.word,
                        state: state,
                        highlight: _query.trim(),
                        onFullPage: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => WordDetailScreen(
                              edition: hit.edition,
                              word: hit.word,
                              state: state,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
