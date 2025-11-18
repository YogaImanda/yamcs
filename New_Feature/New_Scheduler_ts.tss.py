import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  UntypedFormBuilder,
  UntypedFormGroup,
  Validators,
} from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { WebappSdkModule } from '@yamcs/webapp-sdk';

@Component({
  selector: 'app-schedule-script-dialog',
  templateUrl: './schedule-script-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WebappSdkModule],
})
export class ScheduleScriptDialogComponent {
  form: UntypedFormGroup;

  constructor(
    private dialogRef: MatDialogRef<ScheduleScriptDialogComponent>,
    formBuilder: UntypedFormBuilder,
  ) {
    this.form = formBuilder.group({
      // existing fields
      executionTime: ['', [Validators.required]],
      tags: [[], []],

      // NEW: repeat fields
      repeatType: ['none'],        // 'none' | 'interval'
      repeatValue: [1, []],        // nilai interval (default 1)
      repeatUnit: ['hours', []],   // 'minutes' | 'hours' | 'days'
      endDate: [null, []],         // optional, ISO string
    });
  }

  schedule() {
    // dialog akan mengembalikan object:
    // {
    //   executionTime: ...
    //   tags: ...
    //   repeatType: 'none' | 'interval'
    //   repeatValue: number
    //   repeatUnit: 'minutes' | 'hours' | 'days'
    //   endDate: string | null
    // }
    this.dialogRef.close(this.form.value);
  }
}
