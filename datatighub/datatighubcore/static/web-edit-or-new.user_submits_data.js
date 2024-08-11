
function copy() {
    document.getElementById('raw_data_out').select();
    copied = document.execCommand('copy');
    // TODO show user feedback if copied worked/failed
};

