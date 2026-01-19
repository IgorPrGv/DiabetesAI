/**
 * Register Controller
 */
angular.module("registerApp").controller("RegisterCtrl", function($http, $window, $timeout) {
  const vm = this;
  vm.register = { email: "", password: "", confirmPassword: "" };
  vm.authLoading = false;
  vm.registerStatus = "";
  vm.statusClass = "";

  // Check if already logged in - only redirect if logged in
  const storedUserId = localStorage.getItem("session_user_id");
  if (storedUserId) {
    // Has login - check if data is filled
    $http.get(`/api/users/by-auth/${storedUserId}`).then((res) => {
      if (res.data && res.data.id) {
        const profile = res.data.profile_payload || {};
        const isEmpty = !profile.full_name || 
                       !profile.health_metrics?.weight || 
                       !profile.health_metrics?.height ||
                       !profile.health_metrics?.diabetes_type ||
                       !profile.preferences?.cuisine ||
                       !profile.preferences?.region;
        
        if (isEmpty) {
          // Data not filled - redirect to onboarding
          $window.location.href = "/onboarding";
        } else {
          // Data filled - redirect to homepage
          $window.location.href = "/home";
        }
      } else {
        // Profile doesn't exist - redirect to onboarding
        $window.location.href = "/onboarding";
      }
    }).catch(() => {
      // Error checking profile - redirect to onboarding
      $window.location.href = "/onboarding";
    });
  }
  // If no login, just show the register page (user accessed via link)

  vm.registerUser = function() {
    if (vm.register.password !== vm.register.confirmPassword) {
      vm.registerStatus = "As senhas não coincidem";
      vm.statusClass = "error";
      return;
    }

    if (vm.register.password.length < 6) {
      vm.registerStatus = "A senha deve ter pelo menos 6 caracteres";
      vm.statusClass = "error";
      return;
    }

    vm.authLoading = true;
    vm.registerStatus = "";
    vm.statusClass = "";
    
    $http.post("/api/auth/register", {
      email: vm.register.email,
      password: vm.register.password
    }).then((res) => {
      // Don't save session yet - let user login first
      vm.registerStatus = "Conta criada com sucesso! Redirecionando para login...";
      vm.statusClass = "success";
      $timeout(() => {
        // After register, redirect to login (user needs to login)
        $window.location.href = "/login";
      }, 1500);
    }).catch((err) => {
      vm.registerStatus = err.data?.detail || "Falha ao criar conta. Tente novamente.";
      vm.statusClass = "error";
    }).finally(() => {
      vm.authLoading = false;
    });
  };
});

