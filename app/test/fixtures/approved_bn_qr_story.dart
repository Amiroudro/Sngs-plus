import 'package:sarangsho_plus/models.dart';

/// Synthetic, fully reviewed Bengali story used only by UI/layout tests.
/// It deliberately does not reuse or approve any bundled translation overlay.
Story createApprovedBanglaQrStory() {
  return Story(
    id: 'TEST-QR-01',
    headline: 'Bangla QR payment growth slows',
    category: 'Economy',
    summary: 'Daily Bangla QR transactions changed across the reporting period.',
    whyItMatters: 'Digital payment trends help explain changes in cash use.',
    examFacts: 'Bangla QR is an interoperable QR payment system.',
    keyPeople: 'Bangladesh Bank',
    figures: 'Late May: Tk 2-3 billion/day; early October: Tk 13.5 billion/day; late October: Tk 11.9 billion/day',
    sources: const [],
    bn: const BnStory(
      headline: 'বাংলা কিউআর লেনদেনের প্রবৃদ্ধি কমেছে',
      summary: 'মে মাসের শেষ দুই সপ্তাহে দৈনিক লেনদেন ২০০–৩০০ কোটি টাকা ছিল। অক্টোবরের প্রথম সপ্তাহে তা ১,৩৫০ কোটি টাকায় ওঠে। অক্টোবরের শেষ সপ্তাহে তা ১,১৯০ কোটি টাকায় নেমে আসে।',
      whyItMatters: 'লেনদেনের এই পরিবর্তন ডিজিটাল পেমেন্ট ব্যবহারের অগ্রগতি বোঝায়।',
      examFacts: 'বাংলা কিউআর হলো আন্তঃপরিচালনাযোগ্য কিউআর পেমেন্ট ব্যবস্থা।',
      keyPeople: 'বাংলাদেশ ব্যাংক',
      figures: 'মে মাসের শেষ দুই সপ্তাহ: ২০০–৩০০ কোটি টাকা; অক্টোবরের প্রথম সপ্তাহ: ১,৩৫০ কোটি টাকা; অক্টোবরের শেষ সপ্তাহ: ১,১৯০ কোটি টাকা',
      oneLiner: 'বাংলা কিউআর লেনদেনের দৈনিক পরিমাণ অক্টোবরের শেষে কমেছে।',
      keyFacts: [
        KeyFact(label: 'মে মাসের শেষ দুই সপ্তাহ', value: '২০০–৩০০ কোটি টাকা', original: 'Tk 2-3 billion/day'),
        KeyFact(label: 'অক্টোবরের প্রথম সপ্তাহ', value: '১,৩৫০ কোটি টাকা', original: 'Tk 13.5 billion/day'),
        KeyFact(label: 'অক্টোবরের শেষ সপ্তাহ', value: '১,১৯০ কোটি টাকা', original: 'Tk 11.9 billion/day'),
      ],
      whatHappened: [
        'মে মাসের শেষ দুই সপ্তাহে দৈনিক লেনদেন ২০০–৩০০ কোটি টাকা ছিল।',
        'অক্টোবরের প্রথম সপ্তাহে লেনদেন ১,৩৫০ কোটি টাকায় ওঠে।',
        'অক্টোবরের শেষ সপ্তাহে লেনদেন ১,১৯০ কোটি টাকায় নেমে আসে।',
      ],
      examQa: [
        ExamQa(q: 'অক্টোবরের প্রথম সপ্তাহে দৈনিক লেনদেন কত ছিল?', a: '১,৩৫০ কোটি টাকা।'),
      ],
      recallCards: [
        RecallCard(cloze: 'অক্টোবরের প্রথম সপ্তাহে দৈনিক লেনদেন ______ কোটি টাকা ছিল।', answer: '১,৩৫০'),
      ],
      detail: 'বাংলা কিউআর লেনদেনের পরিমাণ মে মাসের শেষ ভাগ থেকে অক্টোবরের শেষ ভাগ পর্যন্ত পরিবর্তিত হয়েছে।',
    ),
  );
}

/// A synthetic edition wrapper for story-screen tests. The approved flag
/// applies only to this in-memory fixture, never to a bundled edition.
Edition createApprovedBanglaQrTestEdition() {
  return Edition(
    date: '2026-11-08',
    status: 'test_fixture',
    stories: [createApprovedBanglaQrStory()],
    words: const [],
    revisionWords: const [],
    phrases: const [],
    mcqs: const [],
    sources: const [],
    counts: const {},
    banglaPendingReview: false,
  );
}
