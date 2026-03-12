import { Component, OnInit } from '@angular/core';

interface FinancialProjection {
  saturation: string;
  users: number;
  price: string;
  revenue: string;
}

@Component({
  selector: 'app-investors',
  templateUrl: './investors.component.html',
  styleUrls: ['./investors.component.scss']
})
export class InvestorsComponent implements OnInit {
  financialProjections: FinancialProjection[] = [
    { saturation: 'Low', users: 1000, price: '$49', revenue: '$588,000' },
    { saturation: 'Medium', users: 5000, price: '$49', revenue: '$2,940,000' },
    { saturation: 'High', users: 10000, price: '$49', revenue: '$5,880,000' }
  ];

  displayedColumns: string[] = ['saturation', 'users', 'price', 'revenue'];

  constructor() { }

  ngOnInit(): void {
  }
}
