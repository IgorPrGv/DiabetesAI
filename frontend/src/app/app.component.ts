import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

type TabId = 'daily' | 'glucose' | 'nutrition' | 'profile';

interface TimelineItem {
  time?: string;
  label: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  type: 'alert' | 'meal' | 'activity' | 'monitoring' | 'snack' | 'medication' | 'hydration';
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  activeTab: TabId = 'daily';
  voiceEnabled = false;

  summaryCards = [
    { label: 'Meals Planned', value: '5', accent: 'green' },
    { label: 'Glucose Checks', value: '1', accent: 'purple' },
    { label: 'Activities', value: '1', accent: 'blue' }
  ];

  timelineItems: TimelineItem[] = [
    {
      label: 'Alert',
      priority: 'high',
      title: 'High Priority',
      description: 'Your morning glucose reading was elevated (156 mg/dL). Reduce carbohydrate intake at breakfast.',
      type: 'alert'
    },
    {
      time: '7:30 AM',
      label: 'Breakfast',
      priority: 'high',
      title: 'Breakfast',
      description: 'Greek yogurt (200g) with berries and chia seeds, green tea',
      type: 'meal'
    },
    {
      time: '8:30 AM',
      label: 'Activity',
      priority: 'medium',
      title: 'Activity',
      description: 'Light walk recommended 30 minutes after breakfast to help regulate glucose',
      type: 'activity'
    },
    {
      time: '10:30 AM',
      label: 'Snack',
      priority: 'medium',
      title: 'Snack',
      description: 'Mid-morning snack: Small apple with 10 almonds',
      type: 'snack'
    },
    {
      time: '12:30 PM',
      label: 'Lunch',
      priority: 'high',
      title: 'Lunch',
      description: 'Grilled chicken salad (150g chicken, mixed greens, olive oil dressing), quinoa (1/2 cup)',
      type: 'meal'
    },
    {
      time: '2:30 PM',
      label: 'Monitoring',
      priority: 'high',
      title: 'Monitoring',
      description: 'Check glucose level 2 hours after lunch',
      type: 'monitoring'
    },
    {
      time: '4:00 PM',
      label: 'Snack',
      priority: 'medium',
      title: 'Snack',
      description: 'Afternoon snack: Carrot sticks with hummus (2 tbsp)',
      type: 'snack'
    },
    {
      time: '6:30 PM',
      label: 'Dinner',
      priority: 'high',
      title: 'Dinner',
      description: 'Baked salmon (150g), steamed broccoli, brown rice (1/2 cup), side salad',
      type: 'meal'
    },
    {
      time: '6:30 PM',
      label: 'Medication',
      priority: 'medium',
      title: 'Medication',
      description: 'Take evening medication with dinner',
      type: 'medication'
    },
    {
      label: 'Hydration',
      priority: 'low',
      title: 'Hydration',
      description: 'Maintain hydration: aim for 8 glasses of water throughout the day',
      type: 'hydration'
    }
  ];

  glucoseAlerts = [
    'Multiple elevated glucose readings detected. Consider reducing carbohydrate portions.',
    'Elevated fasting glucose detected. Consult with your healthcare provider about adjusting evening meal or medication.'
  ];

  glucoseStats = [
    { label: 'Current', value: '145 mg/dL', accent: 'blue' },
    { label: 'Average', value: '141 mg/dL', accent: 'green' },
    { label: 'Est. HbA1c', value: '6.5%', accent: 'purple' },
    { label: 'Trend', value: 'Stable', accent: 'blue' }
  ];

  glucoseSeries = [160, 145, 125, 170, 140, 128, 150];
  glucoseTimes = ['6:00 AM', '8:00 AM', '10:00 AM', '12:00 PM', '2:00 PM', '4:00 PM', '6:00 PM'];

  inventory = [
    {
      title: 'Dairy',
      items: [{ name: 'Greek Yogurt', checked: true }]
    },
    {
      title: 'Protein',
      items: [
        { name: 'Chicken Breast', checked: true },
        { name: 'Salmon', checked: true },
        { name: 'Hummus', checked: true }
      ]
    },
    {
      title: 'Vegetables',
      items: [
        { name: 'Mixed Greens', checked: true },
        { name: 'Broccoli', checked: true }
      ]
    },
    {
      title: 'Fruit',
      items: [{ name: 'Berries', checked: true }]
    },
    {
      title: 'Grains',
      items: [
        { name: 'Quinoa', checked: false },
        { name: 'Brown Rice', checked: true }
      ]
    },
    {
      title: 'Nuts',
      items: [{ name: 'Almonds', checked: true }]
    },
    {
      title: 'Seeds',
      items: [{ name: 'Chia Seeds', checked: true }]
    },
    {
      title: 'Fats',
      items: [{ name: 'Olive Oil', checked: true }]
    }
  ];

  meals = [
    {
      title: 'Breakfast',
      name: 'Greek Yogurt Breakfast Bowl',
      description: 'Greek yogurt with fresh berries and chia seeds',
      calories: '280',
      carbs: '32g',
      protein: '18g',
      fiber: '6g',
      tag: 'low GL',
      availability: 'All ingredients available',
      icon: 'sunrise'
    },
    {
      title: 'Lunch',
      name: 'Grilled Chicken Salad',
      description: 'Mixed greens with grilled chicken and olive oil dressing',
      calories: '420',
      carbs: '28g',
      protein: '38g',
      fiber: '8g',
      tag: 'low GL',
      availability: 'All ingredients available',
      icon: 'sun'
    },
    {
      title: 'Dinner',
      name: 'Baked Salmon Dinner',
      description: 'Salmon with steamed broccoli and brown rice',
      calories: '520',
      carbs: '42g',
      protein: '35g',
      fiber: '7g',
      tag: 'medium GL',
      availability: 'All ingredients available',
      icon: 'moon'
    },
    {
      title: 'Snack',
      name: 'Almond Snack',
      description: 'Small portion of almonds',
      calories: '160',
      carbs: '6g',
      protein: '6g',
      fiber: '3g',
      tag: 'low GL',
      availability: 'All ingredients available',
      icon: 'apple'
    }
  ];

  profile = {
    name: 'Maria Santos',
    age: 58,
    weight: 75,
    height: 165,
    bmi: 27.5,
    bmiLabel: 'Overweight',
    diagnosisDate: '03/15/2020',
    targetRange: '70-140'
  };

  preferences = [
    { label: 'Vegetarian', checked: false },
    { label: 'Low sodium', checked: true },
    { label: 'Mediterranean diet', checked: true },
    { label: 'Dairy-free', checked: false },
    { label: 'Vegan', checked: false },
    { label: 'Low fat', checked: false },
    { label: 'Gluten-free', checked: false }
  ];

  medications = [
    { name: 'Metformin 500mg', checked: true },
    { name: 'Glimepiride 2mg', checked: true },
    { name: 'Insulin Glargine', checked: false },
    { name: 'Metformin 1000mg', checked: false },
    { name: 'Glipizide 5mg', checked: false },
    { name: 'Sitagliptin 100mg', checked: false }
  ];

  setTab(tab: TabId) {
    this.activeTab = tab;
  }

  toggleVoice() {
    this.voiceEnabled = !this.voiceEnabled;
  }

  getChartPoints(): string {
    const max = 200;
    const min = 60;
    const width = 600;
    const height = 200;
    const step = width / (this.glucoseSeries.length - 1);
    return this.glucoseSeries
      .map((value, index) => {
        const normalized = (value - min) / (max - min);
        const x = index * step;
        const y = height - normalized * height;
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(' ');
  }
}

