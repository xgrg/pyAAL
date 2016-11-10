
x = load('$spm_mat_file');
[x.SPM.Ic]=10;
[x.SPM.Im] = false;
[x.SPM.k] = 15;
[x.SPM.pm] = 0.001;
[x.SPM.u] = 0.001;
[x.SPM.thresDesc]='none';
%xSPM = spm_getSPM(x.SPM);
[SPM,xSPM] = spm_getSPM(x.SPM);
%[hreg,xSPM2,SPM2]=spm_results_ui('Setup', x.SPM);
%xSPM2= spm_list(xSPM);
ans = $mode('List', xSPM);
greg_list_dlabels('txtlist', ans);

