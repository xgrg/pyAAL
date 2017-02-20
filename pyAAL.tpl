
x = load('$spm_mat_file');
[x.SPM.Ic]=$contrast;
display('CONTRAST');
display(x.SPM.xCon($contrast).name);
[x.SPM.Im] = false;
[x.SPM.k] = $k;
%[x.SPM.pm] = 0.001;
[x.SPM.u] = $threshold;
[x.SPM.thresDesc]='none';
%xSPM = spm_getSPM(x.SPM);
[SPM,xSPM] = spm_getSPM(x.SPM);
%[hreg,xSPM2,SPM2]=spm_results_ui('Setup', x.SPM);
%xSPM2= spm_list(xSPM);
ans = $mode('List', xSPM);
$mode('txtlist', ans);
