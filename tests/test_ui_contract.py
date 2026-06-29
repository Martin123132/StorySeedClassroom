from __future__ import annotations

from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class UiContractTests(unittest.TestCase):
    def test_next_step_is_an_actionable_route_button(self) -> None:
        html = (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "storyseed_app" / "static" / "app.js").read_text(encoding="utf-8")

        self.assertRegex(html, re.compile(r"<button[^>]*class=\"next-step\"[^>]*id=\"nextStep\"[^>]*type=\"button\"", re.S))
        self.assertNotIn('<div class="next-step" id="nextStep"', html)
        self.assertIn('el("nextStep").addEventListener("click", goNextStep)', js)
        self.assertIn("function nextRoute(items)", js)
        self.assertIn("nextStep.dataset.page = route.target", js)
        self.assertIn('id: "reuse"', js)
        self.assertIn("favouriteCountText", js)
        self.assertIn("Next: Save Favourite", js)
        self.assertIn('currentPage === "favourites" && byId.reuse?.status === "green"', js)

    def test_zone_wallpapers_are_preloaded_and_page_driven(self) -> None:
        js = (PROJECT_ROOT / "storyseed_app" / "static" / "app.js").read_text(encoding="utf-8")
        css = (PROJECT_ROOT / "storyseed_app" / "static" / "app.css").read_text(encoding="utf-8")

        for asset in [
            "storyseed-world-wallpaper.jpg",
            "storyseed-mission-lane.jpg",
            "storyseed-reuse-shelf.jpg",
            "storyseed-prompt-forge.jpg",
            "storyseed-route-map.jpg",
            "storyseed-zone-setup.jpg",
            "storyseed-zone-generate.jpg",
            "storyseed-zone-review.jpg",
            "storyseed-zone-seeds.jpg",
            "storyseed-zone-favourites.jpg",
        ]:
            self.assertIn(asset, js)
            self.assertIn(asset, css)

        self.assertIn("function preloadZoneAssets()", js)
        self.assertIn("function renderRouteMap(items)", js)
        self.assertIn("function renderSidebarRoute(items)", js)
        self.assertIn("function renderZoneBrief(items)", js)
        self.assertIn("function renderMissionStrip(items, route)", js)
        self.assertIn("function activeMissionItem(itemMap, route)", js)
        self.assertIn("function renderEmptyFavourites()", js)
        self.assertIn("function renderBuilderGuide(setup)", js)
        self.assertIn("function renderReviewStation()", js)
        self.assertIn("function reviewStationChecks()", js)
        self.assertIn("function reviewNextAction(checks)", js)
        self.assertIn('id="builderReadout"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('id="reviewChecks"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('id="reviewStationNext"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("Save Current Prompt", js)
        self.assertIn("missionStops", js)
        self.assertIn("navStatusItems", js)
        self.assertIn('class="nav-button active" data-page="start"><span class="light green"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('id="missionSteps"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('id="zoneBriefTitle"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('id="routeStops"', (PROJECT_ROOT / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("preloadZoneAssets();", js)
        self.assertIn("document.body.dataset.page = currentPage", js)
        self.assertIn("@keyframes pageReveal", css)


if __name__ == "__main__":
    unittest.main()
