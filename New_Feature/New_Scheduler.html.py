<h2 mat-dialog-title>Run later</h2>

<mat-dialog-content>
  <div class="hint">
    <p>
      This script will be submitted to the Yamcs Timeline, for execution at a later time.
    </p>
  </div>

  <form [formGroup]="form" class="ya-form">
    <!-- Execution time (existing) -->
    <ya-field label="Execution time">
      <ya-date-time-input
        formControlName="executionTime"
        [showMillis]="true"
        [showNow]="true" />
    </ya-field>

    <!-- Timeline tags (existing) -->
    <ya-field label="Timeline tags" hint="(optional)">
      <ya-help dialogTitle="Timeline Tags">
        Tags allow to categorise items per band. Bands only show items for which one of the tags is
        matching.
      </ya-help>
      <ya-tag-select formControlName="tags" />
    </ya-field>

    <!-- ===================== NEW: Repeat section ===================== -->
    <mat-divider></mat-divider>

    <h3 class="section-title">Repeat options</h3>

    <!-- Pilihan mode repeat -->
    <ya-field label="Mode">
      <mat-radio-group formControlName="repeatType">
        <mat-radio-button value="none">Run once</mat-radio-button>
        <mat-radio-button value="interval">Repeat every…</mat-radio-button>
      </mat-radio-group>
    </ya-field>

    <!-- Konfigurasi interval jika repeatType = 'interval' -->
    <div *ngIf="form.value.repeatType === 'interval'">
      <ya-field label="Interval">
        <div class="interval-row">
          <mat-form-field appearance="outline" class="interval-value">
            <input
              matInput
              type="number"
              min="1"
              formControlName="repeatValue" />
          </mat-form-field>

          <mat-form-field appearance="outline" class="interval-unit">
            <mat-select formControlName="repeatUnit">
              <mat-option value="minutes">Minutes</mat-option>
              <mat-option value="hours">Hours</mat-option>
              <mat-option value="days">Days</mat-option>
            </mat-select>
          </mat-form-field>
        </div>
      </ya-field>

      <ya-field label="End date (optional)">
        <ya-date-time-input formControlName="endDate"></ya-date-time-input>
      </ya-field>
    </div>
    <!-- ============================================================= -->
  </form>
</mat-dialog-content>

<mat-dialog-actions align="end">
  <div style="flex: 1 1 auto"></div>

  <ya-button mat-dialog-close>CANCEL</ya-button>
  <ya-button
    appearance="primary"
    (click)="schedule()"
    [disabled]="!form.valid">
    SCHEDULE
  </ya-button>
</mat-dialog-actions>
