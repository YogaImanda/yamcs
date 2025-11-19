import { ChangeDetectionStrategy, Component } from '@angular/core';
import { FormGroup, UntypedFormBuilder, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import {
  ActivityDefinition,
  AuthService,
  CreateTimelineItemRequest,
  MessageService,
  WebappSdkModule,
  YaHelpDialog,
  YaSelectOption,
  YamcsService,
} from '@yamcs/webapp-sdk';
import { BehaviorSubject } from 'rxjs';
import { ScheduleScriptDialogComponent } from '../schedule-script-dialog/schedule-script-dialog.component';

@Component({
  templateUrl: './run-script.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WebappSdkModule],
})
export class RunScriptComponent {
  form: FormGroup;

  scriptOptions$ = new BehaviorSubject<YaSelectOption[]>([]);

  constructor(
    title: Title,
    formBuilder: UntypedFormBuilder,
    readonly yamcs: YamcsService,
    private messageService: MessageService,
    private authService: AuthService,
    private router: Router,
    private dialog: MatDialog,
  ) {
    title.setTitle('Run a script');
    this.form = formBuilder.group({
      script: ['', [Validators.required]],
      args: [''],
    });

    yamcs.yamcsClient
      .getActivityScripts(this.yamcs.instance!)
      .then((page) => {
        for (const script of page.scripts || []) {
          this.scriptOptions$.next([
            ...this.scriptOptions$.value,
            { id: script, label: script },
          ]);
        }
      })
      .catch((err) => messageService.showError(err));
  }

  runScript() {
    const options = this.createActivityDefinition();
    this.yamcs.yamcsClient
      .startActivity(this.yamcs.instance!, options)
      .then((activity) => {
        if (this.authService.getUser()!.hasSystemPrivilege('ReadActivities')) {
          this.router.navigateByUrl(
            `/activities/${activity.id}?c=${this.yamcs.context}`,
          );
        } else {
          this.dialog
            .open(YaHelpDialog, {
              width: '500px',
              data: {
                icon: 'done',
                closeText: 'OK',
                content: `
                <p>The procedure has started executing.</p>
                <p>
                  Note that you do not have sufficient privileges
                  to follow up on submitted procedures.
                </p>
              `,
              },
            })
            .afterClosed()
            .subscribe(() => this.form.reset());
        }
      })
      .catch((err) => this.messageService.showError(err));
  }

  showSchedule() {
    const capabilities =
      this.yamcs.connectionInfo$.value?.instance?.capabilities || [];
    return (
      capabilities.indexOf('timeline') !== -1 &&
      capabilities.indexOf('activities') !== -1 &&
      this.authService.getUser()!.hasSystemPrivilege('ControlTimeline')
    );
  }

  openScheduleScriptDialog() {
    this.dialog
      .open(ScheduleScriptDialogComponent, {
        width: '600px',
      })
      .afterClosed()
      .subscribe((scheduleOptions) => {
        const formValue = this.form.value;

        if (!scheduleOptions) {
          return;
        }

        const activityDefinition = this.createActivityDefinition();
        const scriptName = formValue['script'];

        // NEW: pilih sekali atau berulang
        if (scheduleOptions.repeatType === 'interval') {
          this.scheduleRepeated(scheduleOptions, scriptName, activityDefinition)
            .then(() => {
              this.messageService.showInfo('Script scheduled (repeated)');
              this.router.navigateByUrl(`/activities?c=${this.yamcs.context}`);
            })
            .catch((err) => this.messageService.showError(err));
        } else {
          // default: sekali saja (behaviour lama)
          this.scheduleOnce(
            scheduleOptions['executionTime'],
            scheduleOptions['tags'],
            scriptName,
            activityDefinition,
          )
            .then(() => {
              this.messageService.showInfo('Script scheduled');
              this.router.navigateByUrl(`/activities?c=${this.yamcs.context}`);
            })
            .catch((err) => this.messageService.showError(err));
        }
      });
  }

  // NEW: fungsi untuk menjadwalkan SATU item timeline (logika lama dipindah ke sini)
  private scheduleOnce(
    startIso: string,
    tags: string[],
    scriptName: string,
    activityDefinition: ActivityDefinition,
  ): Promise<void> {
    const options: CreateTimelineItemRequest = {
      type: 'ACTIVITY',
      duration: '0s',
      name: scriptName,
      start: startIso,
      tags: tags,
      activityDefinition: activityDefinition,
    };

    return this.yamcs.yamcsClient
      .createTimelineItem(this.yamcs.instance!, options)
      .then(() => {});
  }

  // NEW: fungsi untuk menjadwalkan berulang (interval)
  private scheduleRepeated(
    scheduleOptions: any,
    scriptName: string,
    activityDefinition: ActivityDefinition,
  ): Promise<void> {
    const baseMs = new Date(scheduleOptions.executionTime).getTime();

    // Hitung langkah interval dalam ms
    let stepMs = 0;
    if (scheduleOptions.repeatUnit === 'minutes') {
      stepMs = scheduleOptions.repeatValue * 60 * 1000;
    } else if (scheduleOptions.repeatUnit === 'hours') {
      stepMs = scheduleOptions.repeatValue * 60 * 60 * 1000;
    } else if (scheduleOptions.repeatUnit === 'days') {
      stepMs = scheduleOptions.repeatValue * 24 * 60 * 60 * 1000;
    }

    if (stepMs <= 0 || isNaN(stepMs)) {
      // fallback: jadwalkan sekali
      return this.scheduleOnce(
        scheduleOptions.executionTime,
        scheduleOptions.tags,
        scriptName,
        activityDefinition,
      );
    }

    const maxOccurrences = 24; // batas aman
    let endMs: number;

    if (scheduleOptions.endDate) {
      endMs = new Date(scheduleOptions.endDate).getTime();
    } else {
      // kalau tidak ada endDate, jadwalkan sampai 24 kali
      endMs = baseMs + stepMs * (maxOccurrences - 1);
    }

    const promises: Promise<void>[] = [];
    let t = baseMs;
    let count = 0;

    while (t <= endMs && count < maxOccurrences) {
      const iso = new Date(t).toISOString();
      promises.push(
        this.scheduleOnce(
          iso,
          scheduleOptions.tags,
          scriptName,
          activityDefinition,
        ),
      );
      t += stepMs;
      count++;
    }

    return Promise.all(promises).then(() => {});
  }

  private createActivityDefinition(): ActivityDefinition {
    const formValue = this.form.value;
    const options: ActivityDefinition = {
      type: 'SCRIPT',
      args: {
        processor: this.yamcs.processor || null,
        script: formValue['script'],
      },
    };
    if (formValue['args']) {
      options.args!['args'] = formValue['args'];
    }
    return options;
  }
}
