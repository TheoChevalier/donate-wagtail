import "babel-polyfill";
import * as Sentry from "@sentry/browser";

import Tabs from "./components/tabs";
import MenuToggle from "./components/menu-toggle";
import AmountToggle from "./components/donation-amount-toggle";
import CurrencySelect from "./components/currency-selector";
import WayPointDetect from "./components/waypoint-detection";
import DonationCurrencyWidth from "./components/donation-currency-width";
import CopyURL from "./components/copy-url";
import Accordion from "./components/accordion";
import "./components/newsletter";

// Manage tab index for primary nav
function tabIndexer() {
  document.querySelectorAll("[data-nav-tab-index]").forEach(navLink => {
    navLink.tabIndex = "-1";
  });
}

// Open the mobile menu callback
function openMenu() {
  document.querySelector("[data-primary-nav]").classList.add("is-visible");
  document.querySelectorAll("[data-nav-tab-index]").forEach(navLink => {
    navLink.removeAttribute("tabindex");
  });
}

// Close the mobile menu callback
function closeMenu() {
  document.querySelector("[data-primary-nav]").classList.remove("is-visible");
  tabIndexer();
}

document.addEventListener("DOMContentLoaded", function() {
  // Initialize Sentry error reporting
  Sentry.init({ dsn: __SENTRY_DSN__ });

  for (const menutoggle of document.querySelectorAll(MenuToggle.selector())) {
    new MenuToggle(menutoggle, openMenu, closeMenu);
  }

  for (const currencywidth of document.querySelectorAll(
    DonationCurrencyWidth.selector()
  )) {
    new DonationCurrencyWidth(currencywidth);
  }

  for (const donatetoggle of document.querySelectorAll(
    AmountToggle.selector()
  )) {
    new AmountToggle(donatetoggle);
  }

  for (const tabs of document.querySelectorAll(Tabs.selector())) {
    new Tabs(tabs);
  }

  tabIndexer();

  for (const currencySelect of document.querySelectorAll(
    CurrencySelect.selector()
  )) {
    new CurrencySelect(currencySelect);
  }

  WayPointDetect();

  for (const accordion of document.querySelectorAll(Accordion.selector())) {
    new Accordion(accordion);
  }

  for (const copyurl of document.querySelectorAll(CopyURL.selector())) {
    new CopyURL(copyurl);
  }
});
