/**
 * Main Angular Application
 * Componentized structure for DiabetesAI Care
 */

// Register App Module
angular.module("registerApp", []).component("registerComponent", {
  templateUrl: "/static/components/register.html",
  controller: "RegisterCtrl",
  controllerAs: "vm"
});

// Login App Module
angular.module("loginApp", []).component("loginComponent", {
  templateUrl: "/static/components/login.html",
  controller: "LoginCtrl",
  controllerAs: "vm"
});

// Onboarding App Module
angular.module("onboardingApp", []).component("onboardingComponent", {
  templateUrl: "/static/components/onboarding.html",
  controller: "OnboardingCtrl",
  controllerAs: "vm"
});

// Main Diabetes App Module
angular.module("diabetesApp", []).component("homeComponent", {
  templateUrl: "/static/components/home.html",
  controller: "MainCtrl",
  controllerAs: "vm"
});

