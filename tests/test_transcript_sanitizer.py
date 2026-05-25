import unittest
from pathlib import Path

from transcriber_backend import (
    TranscriptSegment,
    format_srt_segments,
    parse_srt_segments,
    sanitize_srt_content,
    sanitize_transcript_segments,
    srt_sanitizer_log_message,
)

FIXTURES_DIR = Path(__file__).with_name("fixtures")


class TranscriptSanitizerTests(unittest.TestCase):
    def test_normal_segments_are_preserved(self):
        segments = [
            TranscriptSegment(0.0, 2.0, "Buongiorno a tutti."),
            TranscriptSegment(2.2, 4.8, "Iniziamo con il primo punto."),
        ]

        self.assertEqual(sanitize_transcript_segments(segments), segments)

    def test_long_banal_run_is_removed(self):
        srt_input = """1
01:31:21,060 --> 01:31:24,860
e poi vi ricordo al termine di firmare l'uscita grazie

2
01:31:33,660 --> 01:31:34,160
e

3
01:32:03,660 --> 01:32:04,160
e

4
01:32:33,660 --> 01:32:34,160
e

5
02:01:10,320 --> 02:01:14,000
Accomodati con noi.
"""

        sanitized_content, removed = sanitize_srt_content(srt_input)
        segments = parse_srt_segments(sanitized_content)

        self.assertEqual(removed, 3)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].text, "e poi vi ricordo al termine di firmare l'uscita grazie")
        self.assertEqual(segments[1].text, "Accomodati con noi.")
        self.assertAlmostEqual(segments[1].start, 7270.32, places=3)

    def test_single_short_segment_is_kept(self):
        segments = [
            TranscriptSegment(10.0, 10.7, "e"),
            TranscriptSegment(11.0, 13.0, "poi passiamo al punto successivo"),
        ]

        self.assertEqual(sanitize_transcript_segments(segments), segments)

    def test_srt_indexes_are_regenerated_after_cleanup(self):
        segments = [
            TranscriptSegment(0.0, 1.0, "ciao"),
            TranscriptSegment(2.0, 2.4, "e"),
            TranscriptSegment(3.0, 3.4, "e"),
            TranscriptSegment(4.0, 4.4, "e"),
            TranscriptSegment(10.0, 12.0, "ripartiamo"),
        ]

        sanitized = sanitize_transcript_segments(segments)
        srt_output = format_srt_segments(sanitized)

        self.assertTrue(srt_output.startswith("1\n00:00:00,000 --> 00:00:01,000\nciao\n"))
        self.assertIn("\n2\n00:00:10,000 --> 00:00:12,000\nripartiamo\n", srt_output)
        self.assertNotIn("\n3\n", srt_output)

    def test_valid_following_timestamps_are_preserved(self):
        segments = [
            TranscriptSegment(5481.06, 5484.86, "e poi vi ricordo al termine di firmare l'uscita grazie"),
            TranscriptSegment(5493.66, 5494.16, "e"),
            TranscriptSegment(5523.66, 5524.16, "e"),
            TranscriptSegment(5553.66, 5554.16, "e"),
            TranscriptSegment(7270.32, 7274.00, "Accomodati con noi."),
        ]

        sanitized = sanitize_transcript_segments(segments)

        self.assertEqual(len(sanitized), 2)
        self.assertAlmostEqual(sanitized[1].start, 7270.32, places=3)
        self.assertAlmostEqual(sanitized[1].end, 7274.00, places=3)

    def test_realistic_repeated_e_fixture_is_sanitized(self):
        fixture_path = FIXTURES_DIR / "repeated_e_after_silence.srt"
        srt_input = fixture_path.read_text(encoding="utf-8")

        sanitized_content, removed = sanitize_srt_content(srt_input)
        sanitized_segments = parse_srt_segments(sanitized_content)

        self.assertEqual(removed, 6)
        self.assertEqual(len(sanitized_segments), 4)

        expected_texts = [
            "Siamo quasi alla pausa, chiudiamo questo passaggio.",
            "Poi riprendiamo con le domande del pubblico.",
            "e poi vi ricordo al termine di firmare l'uscita grazie",
            "Accomodati con noi.",
        ]
        self.assertEqual([segment.text for segment in sanitized_segments], expected_texts)

        self.assertAlmostEqual(sanitized_segments[0].start, 5458.42, places=3)
        self.assertAlmostEqual(sanitized_segments[1].start, 5463.20, places=3)
        self.assertAlmostEqual(sanitized_segments[2].start, 5481.06, places=3)
        self.assertAlmostEqual(sanitized_segments[3].start, 7270.32, places=3)
        self.assertAlmostEqual(sanitized_segments[3].end, 7274.00, places=3)

        self.assertNotIn("\n875\n", sanitized_content)
        self.assertNotIn("\n880\n", sanitized_content)
        self.assertNotIn("\ne\n", sanitized_content)
        self.assertTrue(
            sanitized_content.startswith(
                "1\n01:30:58,420 --> 01:31:02,100\nSiamo quasi alla pausa, chiudiamo questo passaggio.\n"
            )
        )
        self.assertIn(
            "\n4\n02:01:10,320 --> 02:01:14,000\nAccomodati con noi.\n",
            sanitized_content,
        )

    def test_sanitizer_log_message_only_for_removed_segments(self):
        self.assertIsNone(srt_sanitizer_log_message(0))
        self.assertEqual(
            srt_sanitizer_log_message(6),
            "SRT sanitizer: removed 6 degenerate subtitle segments",
        )


if __name__ == "__main__":
    unittest.main()
