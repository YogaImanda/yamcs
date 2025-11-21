import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Title } from '@angular/platform-browser';
import {
  MessageService,
  WebappSdkModule,
  YamcsService,
} from '@yamcs/webapp-sdk';

@Component({
  templateUrl: './schedule-script.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WebappSdkModule],
})
export class ScheduledScriptsComponent {

  loading = true;
  items: any[] = [];
  lastError?: string;

  constructor(
    title: Title,
    readonly yamcs: YamcsService,
    private messageService: MessageService,
  ) {
    title.setTitle('Scheduled scripts');
    this.load();
  }

  /**
   * Ambil daftar scheduled script dari timeline Yamcs.
   * Kita pakai API resmi yamcsClient.getTimelineItems(), sama gaya
   * dengan pemanggilan API lain di RunScriptComponent.
   */
  load() {
    this.loading = true;
    this.lastError = undefined;

    const instance = this.yamcs.instance!;
    const now = new Date();

    // Jendela waktu: 1 hari ke belakang s/d 30 hari ke depan
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    console.log('[ScheduledScripts] load()', { instance, start, stop });

    // cast ke any supaya tidak pusing tipe opsinya
    (this.yamcs.yamcsClient as any)
      .getTimelineItems(instance, {
        start,
        stop,
        detail: true,
      } as any)
      .then((page: any) => {
        console.log('[ScheduledScripts] raw timeline items', page);

        const allItems = page?.items || [];

        // Filter: hanya activity SCRIPT yang statusnya future (PLANNED/SCHEDULED/PENDING)
        this.items = allItems.filter((item: any) => {
          const type = (item.type || '').toUpperCase();
          const detailType = (item.activityDefinition?.type ||
                              item.detail?.type ||
                              '').toUpperCase();

          const status = (
            item.executionStatus ||
            item.activityExecution?.status ||
            item.detail?.executionStatus ||
            ''
          ).toUpperCase();

          const isScript =
            type === 'ACTIVITY' &&
            (detailType === 'SCRIPT' || detailType === 'PROCEDURE');

          const isPlanned =
            status === 'PLANNED' ||
            status === 'SCHEDULED' ||
            status === 'PENDING' ||
            status === 'FUTURE';

          return isScript && isPlanned;
        });

        console.log('[ScheduledScripts] filtered items', this.items);
        this.loading = false;
      })
      .catch((err: any) => {
        console.error('[ScheduledScripts] error', err);
        this.lastError = err?.message || String(err);
        this.messageService.showError(err);
        this.loading = false;
      });
  }
}
