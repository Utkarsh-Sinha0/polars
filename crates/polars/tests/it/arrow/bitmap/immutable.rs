use polars_arrow::array::Splitable;
use polars_arrow::bitmap::Bitmap;
use proptest::prelude::*;

#[test]
fn into_mut_sliced() {
    for offset in [1, 7, 8, 63, 64] {
        let mut values = vec![true; offset];
        values.extend([false, true, false]);
        let bitmap = Bitmap::from(values).sliced(offset, 3);

        let bitmap = bitmap.into_mut().left().unwrap();
        assert_eq!(bitmap.iter().collect::<Vec<_>>(), [false, true, false]);
        assert_eq!(bitmap.unset_bits(), 2);
    }
}

#[test]
fn into_mut_zero_offset_reuses_storage() {
    let bitmap = Bitmap::from([false, true, false, true, true]).sliced(0, 3);
    let ptr = bitmap.as_slice().0.as_ptr();

    let mut mutable = bitmap.into_mut().right().unwrap();
    assert_eq!(mutable.as_slice().as_ptr(), ptr);
    assert_eq!(mutable.iter().collect::<Vec<_>>(), [false, true, false]);
    mutable.push(false);
    assert_eq!(
        mutable.iter().collect::<Vec<_>>(),
        [false, true, false, false]
    );
}

#[test]
fn make_mut_sliced() {
    for offset in [0, 1, 7, 8, 63, 64] {
        for length in [0, 1, 3, 65] {
            let expected: Vec<_> = (0..length).map(|i| i % 3 == 1).collect();
            let mut values = vec![true; offset];
            values.extend(&expected);
            let bitmap = Bitmap::from(values).sliced(offset, length);

            let mut mutable = bitmap.make_mut();
            assert_eq!(mutable.iter().collect::<Vec<_>>(), expected);
            mutable.push(true);
            assert_eq!(
                mutable.iter().collect::<Vec<_>>(),
                expected.into_iter().chain([true]).collect::<Vec<_>>()
            );
        }
    }
}

proptest! {
    #[test]
    fn make_mut_sliced_matches_vec(
        values in proptest::collection::vec(any::<bool>(), 0..257),
        start in 0usize..257,
        size in 0usize..257,
        shared in any::<bool>(),
        cached in any::<bool>(),
        appended in any::<bool>(),
    ) {
        let offset = start % (values.len() + 1);
        let length = size % (values.len() - offset + 1);
        let mut expected = values[offset..offset + length].to_vec();
        let bitmap = Bitmap::from(values).sliced(offset, length);
        if cached {
            prop_assert_eq!(bitmap.unset_bits(), expected.iter().filter(|&&v| !v).count());
        }
        let parent = shared.then(|| bitmap.clone());

        let mut mutable = bitmap.make_mut();
        prop_assert!(mutable.iter().eq(expected.iter().copied()));
        mutable.push(appended);
        if let Some(parent) = parent {
            prop_assert!(parent.iter().eq(expected.iter().copied()));
        }
        expected.push(appended);
        prop_assert_eq!(mutable.iter().collect::<Vec<_>>(), expected);
    }
}

#[test]
fn as_slice() {
    let b = Bitmap::from([true, true, true, true, true, true, true, true, true]);

    let (slice, offset, length) = b.as_slice();
    assert_eq!(slice, &[0b11111111, 0b1]);
    assert_eq!(offset, 0);
    assert_eq!(length, 9);
}

#[test]
fn as_slice_offset() {
    let b = Bitmap::from([true, true, true, true, true, true, true, true, true]);
    let b = b.sliced(8, 1);

    let (slice, offset, length) = b.as_slice();
    assert_eq!(slice, &[0b1]);
    assert_eq!(offset, 0);
    assert_eq!(length, 1);
}

#[test]
fn as_slice_offset_middle() {
    let b = Bitmap::from_u8_slice([0, 0, 0, 0b00010101], 27);
    let b = b.sliced(22, 5);

    let (slice, offset, length) = b.as_slice();
    assert_eq!(slice, &[0, 0b00010101]);
    assert_eq!(offset, 6);
    assert_eq!(length, 5);
}

#[test]
fn split_at_unset_bits() {
    let bm = Bitmap::from_u8_slice([0b01101010, 0, 0, 0b100], 27);

    assert_eq!(bm.unset_bits(), 22);

    let (lhs, rhs) = bm.split_at(5);
    assert_eq!(lhs.lazy_unset_bits(), Some(3));
    assert_eq!(rhs.lazy_unset_bits(), Some(19));

    let (lhs, rhs) = bm.split_at(22);
    assert_eq!(lhs.lazy_unset_bits(), Some(18));
    assert_eq!(rhs.lazy_unset_bits(), Some(4));

    let (lhs, rhs) = bm.split_at(0);
    assert_eq!(lhs.lazy_unset_bits(), Some(0));
    assert_eq!(rhs.lazy_unset_bits(), Some(22));

    let (lhs, rhs) = bm.split_at(27);
    assert_eq!(lhs.lazy_unset_bits(), Some(22));
    assert_eq!(rhs.lazy_unset_bits(), Some(0));

    let bm = Bitmap::new_zeroed(1024);
    let (lhs, rhs) = bm.split_at(512);
    assert_eq!(lhs.lazy_unset_bits(), Some(512));
    assert_eq!(rhs.lazy_unset_bits(), Some(512));

    let bm = Bitmap::new_with_value(true, 1024);
    let (lhs, rhs) = bm.split_at(512);
    assert_eq!(lhs.lazy_unset_bits(), Some(0));
    assert_eq!(rhs.lazy_unset_bits(), Some(0));
}

#[test]
fn debug() {
    let b = Bitmap::from([true, true, false, true, true, true, true, true, true]);
    let b = b.sliced(2, 7);

    assert_eq!(
        format!("{b:?}"),
        "Bitmap { len: 7, offset: 2, bytes: [0b111110__, 0b_______1] }"
    );
}
