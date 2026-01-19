/**
 * Login Controller
 */
angular.module("loginApp").controller("LoginCtrl", function($http, $window, $timeout) {
  const vm = this;
  vm.auth = { email: "", password: "" };
  vm.reset = { email: "" };
  vm.authLoading = false;
  vm.authStatus = "";
  vm.resetStatus = "";
  vm.statusClass = "";
  vm.resetStatusClass = "";
  vm.showReset = false;

  // Check if already logged in - only redirect if logged in
  const storedUserId = localStorage.getItem("session_user_id");
  if (storedUserId) {
    // Has login - check if data is filled
    $http.get(`/api/users/by-auth/${storedUserId}`).then((res) => {
      if (res.data && res.data.id) {
        // Use 'profile' not 'profile_payload'
        const profile = res.data.profile || res.data.profile_payload || {};
        console.log("Login page - Profile data:", profile);
        
        // Check if required fields are filled (not null, not empty string)
        const hasFullName = profile.full_name && profile.full_name.trim() !== "";
        const hasWeight = profile.health_metrics?.weight && profile.health_metrics.weight !== null && profile.health_metrics.weight !== "";
        const hasHeight = profile.health_metrics?.height && profile.health_metrics.height !== null && profile.health_metrics.height !== "";
        const hasDiabetesType = profile.health_metrics?.diabetes_type && profile.health_metrics.diabetes_type.trim() !== "";
        const hasCuisine = profile.preferences?.cuisine && profile.preferences.cuisine.trim() !== "";
        const hasRegion = profile.preferences?.region && profile.preferences.region.trim() !== "";
        
        const isEmpty = !hasFullName || !hasWeight || !hasHeight || !hasDiabetesType || !hasCuisine || !hasRegion;
        
        console.log("Login page - Profile isEmpty?", isEmpty);
        
        if (isEmpty) {
          // Data not filled - redirect to onboarding
          console.log("Login page - Redirecting to onboarding");
          $window.location.href = "/onboarding";
        } else {
          // Data filled - redirect to homepage
          console.log("Login page - Redirecting to home");
          $window.location.href = "/home";
        }
      } else {
        // Profile doesn't exist - redirect to onboarding
        console.log("Login page - No profile found, redirecting to onboarding");
        $window.location.href = "/onboarding";
      }
    }).catch((err) => {
      // Error checking profile - redirect to onboarding
      console.error("Login page - Error checking profile:", err);
      $window.location.href = "/onboarding";
    });
  }
  // If no login, just show the login page (no automatic redirect to register)

  vm.login = function() {
    vm.authLoading = true;
    vm.authStatus = "";
    vm.statusClass = "";
    
    $http.post("/api/auth/login", vm.auth).then((res) => {
      const userId = res.data.user_id;
      localStorage.setItem("session_user_id", String(userId));
      vm.authStatus = "Login realizado com sucesso! Verificando perfil...";
      vm.statusClass = "success";
      
      // Check if user profile is filled
      $http.get(`/api/users/by-auth/${userId}`).then((profileRes) => {
        if (profileRes.data && profileRes.data.id) {
          // Check if profile is empty - use 'profile' not 'profile_payload'
          const profile = profileRes.data.profile || profileRes.data.profile_payload || {};
          console.log("Profile data:", profile);
          console.log("Full name:", profile.full_name);
          console.log("Weight:", profile.health_metrics?.weight);
          console.log("Height:", profile.health_metrics?.height);
          console.log("Diabetes type:", profile.health_metrics?.diabetes_type);
          console.log("Cuisine:", profile.preferences?.cuisine);
          console.log("Region:", profile.preferences?.region);
          
          // Check if required fields are filled (not null, not empty string, not empty object)
          const hasFullName = profile.full_name && profile.full_name.trim() !== "";
          const hasWeight = profile.health_metrics?.weight && profile.health_metrics.weight !== null && profile.health_metrics.weight !== "";
          const hasHeight = profile.health_metrics?.height && profile.health_metrics.height !== null && profile.health_metrics.height !== "";
          const hasDiabetesType = profile.health_metrics?.diabetes_type && profile.health_metrics.diabetes_type.trim() !== "";
          const hasCuisine = profile.preferences?.cuisine && profile.preferences.cuisine.trim() !== "";
          const hasRegion = profile.preferences?.region && profile.preferences.region.trim() !== "";
          
          const isEmpty = !hasFullName || !hasWeight || !hasHeight || !hasDiabetesType || !hasCuisine || !hasRegion;
          
          console.log("Profile isEmpty?", isEmpty);
          console.log("Has required fields:", { hasFullName, hasWeight, hasHeight, hasDiabetesType, hasCuisine, hasRegion });
          
          if (isEmpty) {
            // Data not filled - redirect to onboarding
            console.log("Redirecting to onboarding - profile is empty");
            $timeout(() => {
              $window.location.href = "/onboarding";
            }, 1000);
          } else {
            // Data filled - redirect to homepage
            console.log("Redirecting to home - profile is complete");
            $timeout(() => {
              $window.location.href = "/home";
            }, 1000);
          }
        } else {
          // No profile exists, redirect to onboarding
          console.log("No profile found, redirecting to onboarding");
          $timeout(() => {
            $window.location.href = "/onboarding";
          }, 1000);
        }
      }).catch((err) => {
        // Profile doesn't exist, redirect to onboarding
        console.error("Error checking profile:", err);
        $timeout(() => {
          $window.location.href = "/onboarding";
        }, 1000);
      });
    }).catch((err) => {
      vm.authStatus = err.data?.detail || "Falha no login. Verifique suas credenciais.";
      vm.statusClass = "error";
    }).finally(() => {
      vm.authLoading = false;
    });
  };

  vm.resetPassword = function() {
    vm.authLoading = true;
    vm.resetStatus = "";
    vm.resetStatusClass = "";
    
    // TODO: Implement actual password reset endpoint
    $timeout(() => {
      vm.resetStatus = "Solicitação enviada. Verifique seu email.";
      vm.resetStatusClass = "success";
      vm.authLoading = false;
    }, 600);
  };
});

