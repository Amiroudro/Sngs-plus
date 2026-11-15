/// Editorial tab: NO invented editorials. Only opinion-flavoured
/// content that exists in the data is shown. Neither bundled edition
/// contains any, so this screen honestly shows the designed empty
/// state under its header. When a future edition contains an opinion
/// story, it will appear here automatically as a numbered row.
library;

import 'package:flutter/material.dart';

import '../models.dart';
import '../state/app_state.dart';
import '../widgets/app_theme.dart';
import '../widgets/story_card.dart';
import 'story_detail_screen.dart';

bool isEditorial(Story story) {
  final haystack = '${story.category} ${story.headline}'.toLowerCase();
  return haystack.contains('editorial') ||
      haystack.contains('opinion') ||
      haystack.contains('op-ed') ||
      haystack.contains('analysis') ||
      haystack.contains('commentary') ||
      haystack.contains('সম্পাদকীয়') ||
      haystack.contains('মতামত');
}

class EditorialScreen extends StatelessWidget {
  final AppState state;

  const EditorialScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final edition = state.selectedEdition;
    if (edition == null) {
      return EmptyState(
        icon: Icons.newspaper,
        body: state.t('errorLoading'),
      );
    }
    final editorials = edition.stories.where(isEditorial).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
          child: NewsSectionLabel.heading(state.t('editorial')),
        ),
        if (editorials.isEmpty)
          Expanded(
            child: EmptyState(
              icon: Icons.edit_note,
              title: state.t('editorialEmptyTitle'),
              body: state.t('editorialEmptyBody'),
            ),
          )
        else
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.only(bottom: 16),
              itemCount: editorials.length,
              itemBuilder: (context, i) {
                final story = editorials[i];
                return StoryCard(
                  edition: edition,
                  story: story,
                  state: state,
                  index: i,
                  showDivider: i < editorials.length - 1,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => StoryDetailScreen(
                        edition: edition,
                        story: story,
                        state: state,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}
