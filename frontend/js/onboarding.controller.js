/**
 * Onboarding Controller
 */
angular.module("onboardingApp").controller("OnboardingCtrl", function($http, $window, $timeout, $scope) {
  const vm = this;
  vm.saving = false;
  vm.statusMessage = "";
  vm.statusClass = "";
  vm.progressPercentage = 0;
  
  // Check authentication
  const storedUserId = localStorage.getItem("session_user_id");
  if (!storedUserId) {
    // No session - redirect to login
    $window.location.href = "/login";
    return;
  }
  vm.authUserId = Number(storedUserId);

  // Initialize user structure
  vm.user = {
    full_name: "",
    age: null,
    health_metrics: {
      weight: null,
      height: null,
      bmi: null,
      diabetes_type: "",
      glucose_levels: "",
      blood_pressure: "",
      other_conditions: []
    },
    preferences: {
      cuisine: "",
      region: "",
      likes: [],
      dislikes: []
    },
    restrictions: [],
    allergies: [],
    goals: [],
    inventory: []
  };

  vm.otherConditionsText = "";
  vm.likesText = "";
  vm.dislikesText = "";
  vm.restrictionsText = "";
  vm.allergiesText = "";
  vm.goalsText = "";
  vm.inventoryText = "";

  vm.calculateBMI = function() {
    const weight = vm.user.health_metrics.weight;
    const height = vm.user.health_metrics.height;
    if (weight && height && height > 0) {
      const heightM = height / 100;
      const bmi = weight / (heightM * heightM);
      vm.user.health_metrics.bmi = Math.round(bmi * 10) / 10;
      return `IMC: ${vm.user.health_metrics.bmi}`;
    }
    return "Preencha peso e altura para calcular o IMC";
  };

  vm.calculateProgress = function() {
    let filled = 0;
    let total = 6; // Required fields
    if (vm.user.full_name) filled++;
    if (vm.user.health_metrics.weight) filled++;
    if (vm.user.health_metrics.height) filled++;
    if (vm.user.health_metrics.diabetes_type) filled++;
    if (vm.user.preferences.cuisine) filled++;
    if (vm.user.preferences.region) filled++;
    return Math.round((filled / total) * 100);
  };

  // Watch for changes in user data to update progress
  $scope.$watch(function() {
    return vm.user;
  }, function() {
    vm.progressPercentage = vm.calculateProgress();
  }, true);

  vm.saveProfile = function() {
    vm.saving = true;
    vm.statusMessage = "";
    vm.statusClass = "";

    // Process text fields into arrays
    if (vm.otherConditionsText) {
      vm.user.health_metrics.other_conditions = vm.otherConditionsText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.likesText) {
      vm.user.preferences.likes = vm.likesText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.dislikesText) {
      vm.user.preferences.dislikes = vm.dislikesText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.restrictionsText) {
      vm.user.restrictions = vm.restrictionsText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.allergiesText) {
      vm.user.allergies = vm.allergiesText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.goalsText) {
      vm.user.goals = vm.goalsText.split(',').map(s => s.trim()).filter(s => s);
    }
    if (vm.inventoryText) {
      vm.user.inventory = vm.inventoryText.split(',').map(s => s.trim()).filter(s => s);
    }

    // Prepare profile data - ensure all fields are properly formatted
    const profileData = {
      full_name: vm.user.full_name || null,
      age: vm.user.age || null,
      health_metrics: {
        weight: vm.user.health_metrics.weight || null,
        height: vm.user.health_metrics.height || null,
        bmi: vm.user.health_metrics.bmi || null,
        diabetes_type: vm.user.health_metrics.diabetes_type || null,
        glucose_levels: vm.user.health_metrics.glucose_levels || null,
        blood_pressure: vm.user.health_metrics.blood_pressure || null,
        other_conditions: vm.user.health_metrics.other_conditions || []
      },
      preferences: {
        cuisine: vm.user.preferences.cuisine || null,
        region: vm.user.preferences.region || null,
        likes: vm.user.preferences.likes || [],
        dislikes: vm.user.preferences.dislikes || []
      },
      restrictions: vm.user.restrictions || [],
      allergies: vm.user.allergies || [],
      goals: vm.user.goals || [],
      inventory: vm.user.inventory || []
    };

    // Get or create user profile
    $http.get(`/api/users/by-auth/${vm.authUserId}`).then((res) => {
      const userId = res.data.id;
      
      // Update existing profile
      console.log("Saving profile data:", profileData);
      $http.put(`/api/users/${userId}`, profileData).then((response) => {
        // Verify data was saved correctly - use 'profile' not 'profile_payload'
        console.log("Profile saved response:", response.data);
        const savedProfile = response.data.profile || response.data.profile_payload || {};
        console.log("Saved profile:", savedProfile);
        console.log("Full name:", savedProfile.full_name);
        console.log("Weight:", savedProfile.health_metrics?.weight);
        console.log("Height:", savedProfile.health_metrics?.height);
        console.log("Diabetes type:", savedProfile.health_metrics?.diabetes_type);
        console.log("Cuisine:", savedProfile.preferences?.cuisine);
        console.log("Region:", savedProfile.preferences?.region);
        
        // Double-check that required fields are saved (not null, not empty string)
        const hasFullName = savedProfile.full_name && savedProfile.full_name.trim() !== "";
        const hasWeight = savedProfile.health_metrics?.weight && savedProfile.health_metrics.weight !== null && savedProfile.health_metrics.weight !== "";
        const hasHeight = savedProfile.health_metrics?.height && savedProfile.health_metrics.height !== null && savedProfile.health_metrics.height !== "";
        const hasDiabetesType = savedProfile.health_metrics?.diabetes_type && savedProfile.health_metrics.diabetes_type.trim() !== "";
        const hasCuisine = savedProfile.preferences?.cuisine && savedProfile.preferences.cuisine.trim() !== "";
        const hasRegion = savedProfile.preferences?.region && savedProfile.preferences.region.trim() !== "";
        
        const hasRequiredFields = hasFullName && hasWeight && hasHeight && hasDiabetesType && hasCuisine && hasRegion;
        
        console.log("Has all required fields?", hasRequiredFields);
        console.log("Field checks:", { hasFullName, hasWeight, hasHeight, hasDiabetesType, hasCuisine, hasRegion });
        
        if (hasRequiredFields) {
          vm.statusMessage = "Perfil salvo com sucesso! Redirecionando...";
          vm.statusClass = "success";
          $timeout(() => {
            // Redirect to home - data is now saved
            console.log("Redirecting to /home");
            $window.location.href = "/home";
          }, 1500);
        } else {
          console.error("Required fields missing:", {
            full_name: savedProfile.full_name,
            weight: savedProfile.health_metrics?.weight,
            height: savedProfile.health_metrics?.height,
            diabetes_type: savedProfile.health_metrics?.diabetes_type,
            cuisine: savedProfile.preferences?.cuisine,
            region: savedProfile.preferences?.region
          });
          vm.statusMessage = "Erro: Dados não foram salvos corretamente. Verifique o console para mais detalhes.";
          vm.statusClass = "error";
          vm.saving = false;
        }
      }).catch((err) => {
        console.error("Error saving profile:", err);
        vm.statusMessage = err.data?.detail || "Erro ao salvar perfil";
        vm.statusClass = "error";
        vm.saving = false;
      });
    }).catch(() => {
      // Create new profile if doesn't exist
      const createData = {
        auth_user_id: vm.authUserId,
        ...profileData
      };
      
      console.log("Creating profile data:", createData);
      $http.post("/api/users", createData).then((response) => {
        // Verify data was saved correctly - use 'profile' not 'profile_payload'
        console.log("Profile created response:", response.data);
        const savedProfile = response.data.profile || response.data.profile_payload || {};
        console.log("Saved profile:", savedProfile);
        console.log("Full name:", savedProfile.full_name);
        console.log("Weight:", savedProfile.health_metrics?.weight);
        console.log("Height:", savedProfile.health_metrics?.height);
        console.log("Diabetes type:", savedProfile.health_metrics?.diabetes_type);
        console.log("Cuisine:", savedProfile.preferences?.cuisine);
        console.log("Region:", savedProfile.preferences?.region);
        
        // Double-check that required fields are saved (not null, not empty string)
        const hasFullName = savedProfile.full_name && savedProfile.full_name.trim() !== "";
        const hasWeight = savedProfile.health_metrics?.weight && savedProfile.health_metrics.weight !== null && savedProfile.health_metrics.weight !== "";
        const hasHeight = savedProfile.health_metrics?.height && savedProfile.health_metrics.height !== null && savedProfile.health_metrics.height !== "";
        const hasDiabetesType = savedProfile.health_metrics?.diabetes_type && savedProfile.health_metrics.diabetes_type.trim() !== "";
        const hasCuisine = savedProfile.preferences?.cuisine && savedProfile.preferences.cuisine.trim() !== "";
        const hasRegion = savedProfile.preferences?.region && savedProfile.preferences.region.trim() !== "";
        
        const hasRequiredFields = hasFullName && hasWeight && hasHeight && hasDiabetesType && hasCuisine && hasRegion;
        
        console.log("Has all required fields?", hasRequiredFields);
        console.log("Field checks:", { hasFullName, hasWeight, hasHeight, hasDiabetesType, hasCuisine, hasRegion });
        
        if (hasRequiredFields) {
          vm.statusMessage = "Perfil criado com sucesso! Redirecionando...";
          vm.statusClass = "success";
          $timeout(() => {
            // Redirect to home - data is now saved
            console.log("Redirecting to /home");
            $window.location.href = "/home";
          }, 1500);
        } else {
          console.error("Required fields missing:", {
            full_name: savedProfile.full_name,
            weight: savedProfile.health_metrics?.weight,
            height: savedProfile.health_metrics?.height,
            diabetes_type: savedProfile.health_metrics?.diabetes_type,
            cuisine: savedProfile.preferences?.cuisine,
            region: savedProfile.preferences?.region
          });
          vm.statusMessage = "Erro: Dados não foram salvos corretamente. Verifique o console para mais detalhes.";
          vm.statusClass = "error";
          vm.saving = false;
        }
      }).catch((err) => {
        console.error("Error creating profile:", err);
        vm.statusMessage = err.data?.detail || "Erro ao criar perfil";
        vm.statusClass = "error";
        vm.saving = false;
      });
    });
  };
});
