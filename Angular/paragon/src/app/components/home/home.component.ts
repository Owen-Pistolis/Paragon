import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit {

  cols: number = 2;

  constructor(private router: Router, private breakpointObserver: BreakpointObserver) {
    this.breakpointObserver.observe([Breakpoints.Handset, Breakpoints.Tablet]).subscribe(result => {
      this.cols = result.matches ? 1 : 2; // 1 column on mobile and tablets, 2 otherwise
    });
   }

  ngOnInit(): void {
  }
  goToParagon(){
    this.router.navigate(["/about/paragon"]);
  }
  goToPrometheus(){
    this.router.navigate(["/about/prometheus"]);
  }
  goToInvestors(){
    this.router.navigate(["/investors"]);
  }

}
