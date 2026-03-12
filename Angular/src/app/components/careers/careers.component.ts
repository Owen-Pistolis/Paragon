import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { Job } from 'src/app/types/job';
import { firstValueFrom } from 'rxjs'
import { MatDialog } from '@angular/material/dialog'
import { Router } from '@angular/router';

@Component({
  selector: 'app-careers',
  standalone: false,
  templateUrl: './careers.component.html',
  styleUrls: ['./careers.component.scss']
})
export class CareersComponent implements OnInit {

  jobs: Job[] = []
  readonly dialog = inject(MatDialog);
  constructor(private http: HttpClient, private router: Router) { }

  ngOnInit(): void {
    this.getJobs();
  }
  openApplication(){
    //const applicationRef = this.dialog.open()
  }

  async getJobs() {
    try {
      const data: Job[] = await firstValueFrom(this.http.get<Job[]>('assets/jobs.json'));
      this.jobs = data;
      console.log(this.jobs);  // Log after the data is assigned
    } catch (error) {
      console.error('Error reading jobs', error);
    }
  }
  apply(job: Job){
    this.router.navigate(["/apply"], { state: { job } });
  }
}
