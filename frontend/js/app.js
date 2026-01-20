/**
 * Main Angular Application
 * Componentized structure for DiabetesAI Care
 */

// Register App Module
angular.module("registerApp", []).component("registerComponent", {
  templateUrl: "/components/register.html",
  controller: "RegisterCtrl",
  controllerAs: "vm"
});

// Login App Module
angular.module("loginApp", []).component("loginComponent", {
  templateUrl: "/components/login.html",
  controller: "LoginCtrl",
  controllerAs: "vm"
});

// Onboarding App Module
angular.module("onboardingApp", []).component("onboardingComponent", {
  templateUrl: "/components/onboarding.html",
  controller: "OnboardingCtrl",
  controllerAs: "vm"
});

// Main Diabetes App Module
angular.module("diabetesApp", []).component("homeComponent", {
  templateUrl: "/components/home.html",
  controller: "MainCtrl",
  controllerAs: "vm"
});

