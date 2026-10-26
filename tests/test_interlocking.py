import unittest
from backend.controller.interlocking_system import InterlockingSystem
from backend.model.models import RailwayLine

class InterlockingTests(unittest.TestCase):
    def test_unknown_station_does_not_return_a_fake_platform(self):
        interlocking = InterlockingSystem()
        self.assertIsNone(interlocking.allocate_platform(42, "NOT_A_STATION"))

    def test_release_track_section_keeps_unrelated_train_blocks(self):
        interlocking = InterlockingSystem()
        infrastructure = [RailwayLine("A", "B", False), RailwayLine("C", "D", False)]
        ab = interlocking._get_undirected_key("A", "B")
        cd = interlocking._get_undirected_key("C", "D")
        interlocking.single_track_locks[ab] = (1, ("A", "B"))
        interlocking.single_track_locks[cd] = (1, ("C", "D"))
        interlocking.directional_blocks[("A", "B")] = 1
        interlocking.directional_blocks[("C", "D")] = 1

        interlocking.release_track_section(1, "A", "B", infrastructure)

        self.assertIsNone(interlocking.single_track_locks[ab])
        self.assertEqual(interlocking.single_track_locks[cd], (1, ("C", "D")))
        self.assertIsNone(interlocking.directional_blocks[("A", "B")])
        self.assertEqual(interlocking.directional_blocks[("C", "D")], 1)

if __name__ == "__main__":
    unittest.main()
