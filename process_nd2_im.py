import matplotlib
matplotlib.use('agg')
import sys
import os
import fastqimagecorrelator
import local_config
import nd2reader
import nd2tools


def get_align_params(align_param_fpath):
    #d = {name: value for line in open(align_param_fpath) for name, value in line.strip().split()}
    d = {}
    for line in open(align_param_fpath):
        if not line.strip():
            continue
        name, value = line.strip().split()
        d[name] = value

    try:
        strategy = d['strategy']
    except:
        strategy = 'slow'
    assert strategy in ['fast', 'slow'], strategy

    try:
        snr_thresh = float(d['snr_thresh'])
    except:
        snr_thresh = 1.2

    try:
        min_hits = int(d['min_hits'])
    except:
        min_hits = 15

    return (d['project_name'],
            d['aligning_read_names_fpath'],
            d['all_read_names_fpath'],
            int(d['objective']),
            float(d['rotation_est']),
            float(d['fq_w_est']),
            int(d['min_tile_num']),
            int(d['max_tile_num']),
            strategy,
            snr_thresh,
            min_hits
           )


def fast_possible_tile_keys(nd2, im_idx, min_tile, max_tile):
    coord_info, xs, ys, zs, pos_names, rows, cols = nd2tools.get_nd2_image_coord_info(nd2)
    cols.sort()
    pos_name = nd2tools.convert_nd2_coordinates(nd2, im_idx=im_idx, outfmt='pos_name')
    col_idx = cols.index(pos_name[1:])
    expected_tile = int(min_tile + col_idx * float(max_tile - min_tile)/(len(cols)-1))
    return tile_keys_given_nums(range(expected_tile - 1, expected_tile + 2))


def tile_keys_given_nums(tile_nums):
    return ['lane1tile{0}'.format(tile_num) for tile_num in tile_nums]


def process_fig(align_run_name, nd2_fpath, align_param_fpath, im_idx):
    im_idx = int(im_idx)
    project_name, aligning_read_names_fpath, all_read_names_fpath, objective, rotation_est, fq_w_est, \
            min_tile_num, max_tile_num, strategy, snr_thresh, min_hits = get_align_params(align_param_fpath)
    nd2 = nd2reader.Nd2(nd2_fpath)
    if strategy == 'fast':
        possible_tile_keys = fast_possible_tile_keys(nd2, im_idx, min_tile_num, max_tile_num)
    elif strategy == 'slow':
        possible_tile_keys = tile_keys_given_nums(range(min_tile_num, max_tile_num+1))
    bname = os.path.splitext(os.path.basename(nd2_fpath))[0]
    sexcat_fpath = os.path.join(os.path.splitext(nd2_fpath)[0], '%d.cat' % im_idx)
    
    fig_dir = os.path.join(local_config.fig_dir, align_run_name, bname)
    results_dir = os.path.join(local_config.base_dir, 'results', align_run_name, bname)
    for d in [fig_dir, results_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
    all_read_rcs_fpath = os.path.join(results_dir, '{}_all_read_rcs.txt'.format(im_idx))

    if os.path.isfile(all_read_rcs_fpath):
        print bname, im_idx, ' already done.'

    intensity_fpath = os.path.join(results_dir, '{}_intensities.txt'.format(im_idx))
    stats_fpath = os.path.join(results_dir, '{}_stats.txt'.format(im_idx))
    fic = fastqimagecorrelator.FastqImageAligner(project_name)
    tile_data=local_config.fastq_tiles_given_read_name_fpath(aligning_read_names_fpath)
    fic.load_reads(tile_data)
    fic.set_image_data(im=nd2[im_idx], objective=objective, fpath=str(im_idx), median_normalize=True)
    fic.set_sexcat_from_file(sexcat_fpath)
    fic.align(possible_tile_keys, rotation_est, fq_w_est, snr_thresh=snr_thresh, min_hits=min_hits, hit_type=['exclusive', 'good_mutual'])
    print project_name, bname, im_idx, ','.join(tile.key for tile in fic.hitting_tiles)
    
    fic.output_intensity_results(intensity_fpath)
    fic.write_alignment_stats(stats_fpath)

    ax = fic.plot_all_hits()
    ax.figure.savefig(os.path.join(fig_dir, '{}_all_hits.pdf'.format(im_idx)))

    ax = fic.plot_hit_hists()
    ax.figure.savefig(os.path.join(fig_dir, '{}_hit_hists.pdf'.format(im_idx)))

    all_fic = fastqimagecorrelator.FastqImageAligner(project_name)
    tile_data = local_config.fastq_tiles_given_read_name_fpath(all_read_names_fpath)
    all_fic.all_reads_fic_from_aligned_fic(fic, tile_data)
    all_fic.write_read_names_rcs(all_read_rcs_fpath)

if __name__ == '__main__':
    fmt = '{0} <align_run_name> <nd2_fpath> <align_param_file> <im_idx>'.format(sys.argv[0])
    if len(sys.argv) != len(fmt.split()):
        sys.exit('Usage: ' + fmt)
    process_fig(*sys.argv[1:])
    print("donezo!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
